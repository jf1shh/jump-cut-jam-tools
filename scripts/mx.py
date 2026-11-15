#!/usr/bin/env python3
"""mx.py - context-cheap helper for the Unreal MCP server (http://127.0.0.1:8010/mcp). Standard library only.

  mx.py shot LABEL ['{"actor":"SM_Crate"}']      screenshot via step_shot.py; prints the PNG path
  mx.py call TOOLSET TOOL ['{"arg": 1}']         call_tool; output capped (--max-chars 800), --save PATH keeps all
  mx.py describe TOOLSET [--grep RE] [--refresh] describe a toolset ONCE (5.8.4 describe_toolset / 5.9 describe_toolsets), cache it, print excerpts
  mx.py toolsets [--grep RE]                     list_toolsets, cached, excerpts only
  mx.py py SCRIPT|-                              run Python in the editor (string arg on 5.8.4, CodeBlock on 5.9); prints the result
  mx.py save                                     save all dirty assets (5.8: AssetTools.save_assets, empty list;
                                                 5.9: the editor's save_dirty_packages, the AssetToolset has save_asset only)

TOOLSET may be the full name (editor_toolset.toolsets.blueprint.BlueprintTools) or a short suffix
(BlueprintTools) once `toolsets` has been run. JSON args: '-' reads stdin. Output is always small on purpose:
read a saved file with `peek --grep` or `jq`, do not print it.

Gotchas (each one cost a mock session minutes):
  * Port: the editor serves 8010. Other port: --url http://127.0.0.1:PORT/mcp or MEGAJAM_MCP_URL.
  * The server has only a few top-level tools; the real tools sit inside toolsets and run through call_tool
    (toolset_name, tool_name, arguments). 5.8.4: list_toolsets, describe_toolset(toolset_name), call_tool.
    5.9: list_toolsets, describe_toolsets(toolset_names[], include_schemas), describe_tools(tool_names[]), call_tool.
    mx.py probes tools/list once and picks the shape; 5.8.4 stays the fallback. A 5.9 execute_python takes
    {"script": {"Content": SRC, "Language": "Python"}} (a CodeBlock) and returns the last expression's value.
  * exec_tool_script only calls toolset tools; it cannot run arbitrary Python (use the python tool for that).
  * BlueprintTools.add_variable types: bool, int, float, Vector (no others worked).
  * set_properties `values` is a JSON STRING, not an object.
  * Graph DSL: event names EventTick and EventReceiveDrawHUD (add_event first); sin is Math|Trig|Sin(Degrees);
    other-object variable path is Class|BPKid|GetState.
  * No MCP save-all: use `mx.py save` (5.8 AssetTools.save_assets with empty paths; 5.9 editor Python).
  * get_properties on a CDO needs BlueprintTools.get_default_object first.
  * find_actors needs its required params (tag etc.); a bad call prints the required list from the cached describe.
  * merge_actors prefixes names with SM_.

State dir: $MX_DIR, else $CLAUDE_JOB_DIR/mx, else ./work/mx (describe/<toolset>.json, toolsets.json, calls/).
Exit: 0 ok, 1 tool error, 2 usage or editor unreachable.
"""
import argparse
import hashlib
import shutil
import json
import time
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from mcp_call import McpClient, McpError, EXIT_TOOL, EXIT_CONN, DEFAULT_URL  # noqa: E402

ERR_CAP = 300
SAVE_TOOLSET = "editor_toolset.toolsets.asset.AssetTools"  # 5.8.4 only; 5.9 renamed it AssetToolset and has no save-all
SAVE_PY_59 = "import unreal\nunreal.EditorLoadingAndSavingUtils.save_dirty_packages(True, True)"


def state_dir():
    d = os.environ.get("MX_DIR")
    if not d:
        job = os.environ.get("CLAUDE_JOB_DIR")
        d = os.path.join(job, "mx") if job else os.path.join("work", "mx")
    return d


def url_state_dir(url=None):
    """State dir for ONE editor: keyed by the resolved URL (--url, else MEGAJAM_MCP_URL, else the default), so a
    toolset/describe cache left by another editor is never trusted. mx.py and standalone step_shot share this."""
    resolved = url or os.environ.get("MEGAJAM_MCP_URL", DEFAULT_URL)
    return os.path.join(state_dir(), "url-" + hashlib.sha1(resolved.encode()).hexdigest()[:10])


def clip(text, n):
    text = str(text)
    if n <= 0 or len(text) <= n:
        return text
    return text[:n] + f"... [+{len(text) - n} chars cut]"


def result_text(res):
    parts = [c.get("text", "") for c in res.get("content", []) if isinstance(c, dict) and c.get("type") == "text"]
    return "\n".join(parts) if parts else json.dumps(res)


def safe_name(name):
    return re.sub(r"[^A-Za-z0-9_.-]", "_", name)[:120] or hashlib.sha1(name.encode()).hexdigest()


def raw_call(cli, tool, args):
    """tools/call returning (text, is_error). RPC-level failures raise McpError."""
    cli.connect()
    res = cli.request("tools/call", {"name": tool, "arguments": args})
    return result_text(res), bool(res.get("isError"))


def top_describe(cli, toolset):
    if describe_flavor(cli) == "new":
        text, err = raw_call(cli, "describe_toolsets", {"toolset_names": [toolset], "include_schemas": True})
        if not err:  # 5.9 reports an unknown name in an "errors" map, not as isError
            try:
                data = json.loads(text)
            except ValueError:
                data = None
            if isinstance(data, dict) and isinstance(data.get("errors"), dict) and data["errors"] and not data.get("toolsets"):
                return json.dumps(data["errors"]), True
        return text, err
    return raw_call(cli, "describe_toolset", {"toolset_name": toolset})


_FLAVORS = {}  # url -> flavor, so cmd_py/cmd_shot/step_shot (each builds a client) probe tools/list once


def describe_flavor(cli, fresh=False):
    """'new' (UE 5.9: describe_toolsets) or 'old' (5.8.4: describe_toolset), from one tools/list probe, cached
    per client and per URL. A tools/list error is retried once, then raised: guessing 'old' sent a 5.9 server
    the removed describe_toolset. fresh=True re-probes (the editor on the URL may have been swapped)."""
    flavor = None if fresh else getattr(cli, "_flavor", None) or _FLAVORS.get(cli.url)
    if flavor is None:
        cli.connect()
        for attempt in (1, 2):
            try:
                names = {t.get("name") for t in cli.request("tools/list").get("tools", [])}
                break
            except McpError as e:
                if e.exit_code == EXIT_CONN or attempt == 2:
                    raise
        flavor = "new" if "describe_toolsets" in names else "old"
    cli._flavor = _FLAVORS[cli.url] = flavor
    return flavor


def sync_cache(cli, sd):
    """Both engines serve the same URL, so the URL-keyed cache dir can hold the OTHER engine's toolsets.json and
    describe/*.json (5.8 dotted names vs 5.9 plain ones). A flavor marker in the dir; on a mismatch (or no
    marker) the cache is wiped. Does nothing, and never probes, when there is no cache yet or the editor is down."""
    marker = os.path.join(sd, "flavor")
    if not (os.path.exists(os.path.join(sd, "toolsets.json")) or os.path.isdir(os.path.join(sd, "describe"))):
        return
    try:
        flavor = describe_flavor(cli, fresh=True)
    except McpError:
        return
    have = open(marker).read().strip() if os.path.exists(marker) else None
    if have != flavor:
        shutil.rmtree(os.path.join(sd, "describe"), ignore_errors=True)
        if os.path.exists(os.path.join(sd, "toolsets.json")):
            os.remove(os.path.join(sd, "toolsets.json"))
        write(marker, flavor)


def mark_flavor(cli, sd):
    """Stamp a freshly written cache with the flavor it came from."""
    try:
        flavor = describe_flavor(cli)
    except McpError:
        return
    write(os.path.join(sd, "flavor"), flavor)


def listed_toolsets(text, flavor):
    """Toolset names in list_toolsets output. 5.9 names have no dots (PythonScriptingTools), so read the JSON."""
    if flavor == "new":
        try:
            data = json.loads(text)
        except ValueError:
            data = None
        found = []

        def walk(o, top):
            if isinstance(o, dict):
                if isinstance(o.get("toolsets"), dict):
                    found.extend(k for k in o["toolsets"] if isinstance(k, str))
                if isinstance(o.get("name"), str):
                    found.append(o["name"])
                elif top:
                    found.extend(k for k in o if isinstance(k, str) and k not in ("toolsets", "errors"))
                for v in o.values():
                    walk(v, False)
            elif isinstance(o, list):
                for v in o:
                    if isinstance(v, str) and not top:
                        found.append(v)
                    else:
                        walk(v, False)
        walk(data, True)
        if found:
            return sorted(set(found))
    return names_in(text)


def names_in(text):
    """Strings that look like dotted toolset names, from list_toolsets output.

    UE 5.9 answers with a bullet list ("- Name: description ...") whose prose holds dotted words
    (AGENTS.md, e.g., csv.bin, NodeName.PinName). When bullets are there, only the bullet names count;
    otherwise every dotted word does (older output)."""
    bullets = re.findall(r"^\s*[-*]\s+([A-Za-z_][\w]*(?:\.[A-Za-z_][\w]*)+)\s*:", text, re.M)
    if bullets:
        return sorted(set(bullets))
    return sorted(set(re.findall(r"[A-Za-z_][\w]*(?:\.[A-Za-z_][\w]*)+", text)))


def resolve_toolset(name, sd):
    if "." in name:
        return name
    p = os.path.join(sd, "toolsets.json")
    if os.path.exists(p):
        hits = [n for n in names_in(open(p).read()) if n.endswith("." + name)]
        if len(hits) == 1:
            return hits[0]
        if len(hits) > 1:
            raise McpError(f"short name {name!r} is ambiguous: {', '.join(hits[:5])}", 2)
    return name


def write(path, text):
    os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
    with open(path, "w") as f:
        f.write(text)


def cached_describe(cli, toolset, sd, refresh=False):
    p = os.path.join(sd, "describe", safe_name(toolset) + ".json")
    if refresh or not os.path.exists(p):
        text, err = top_describe(cli, toolset)
        if err:
            raise McpError(f"describe {toolset} failed: {clip(text, ERR_CAP)}", EXIT_TOOL)
        write(p, text)
        mark_flavor(cli, sd)
    with open(p) as f:
        return p, f.read()


def find_tool_node(obj, tool):
    if isinstance(obj, dict):
        if obj.get("name") == tool and any(k in obj for k in ("inputSchema", "parameters", "arguments", "params", "required")):
            return obj
        for v in obj.values():
            r = find_tool_node(v, tool)
            if r:
                return r
    elif isinstance(obj, list):
        for v in obj:
            r = find_tool_node(v, tool)
            if r:
                return r
    return None


def param_hint(text, tool):
    """Best-effort 'required: a, b; optional: c' for TOOL from describe text. '' when unknown."""
    try:
        node = find_tool_node(json.loads(text), tool)
    except ValueError:
        node = None
    if not node:
        return ""
    schema = node.get("inputSchema") or node.get("parameters") or node.get("arguments") or node
    req, props = [], []
    if isinstance(schema, dict):
        req = [r for r in schema.get("required", []) if isinstance(r, str)]
        p = schema.get("properties")
        props = list(p) if isinstance(p, dict) else []
    elif isinstance(schema, list):
        for a in schema:
            if isinstance(a, dict) and a.get("name"):
                props.append(a["name"])
                if a.get("required"):
                    req.append(a["name"])
    opt = [p for p in props if p not in req]
    return f"required: {', '.join(req) or '(none listed)'}; optional: {', '.join(opt[:12]) or '-'}"


def cmd_call(a, cli, sd):
    raw = sys.stdin.read() if a.args == "-" else a.args
    try:
        args = json.loads(raw)
    except ValueError as e:
        print(f"mx: bad JSON args: {e}", file=sys.stderr)
        return 2
    sync_cache(cli, sd)
    toolset = resolve_toolset(a.toolset, sd)
    outer = {"toolset_name": toolset, "tool_name": a.tool, "arguments": args}
    try:
        text, err = raw_call(cli, "call_tool", outer)
    except McpError as e:
        text, err = str(e), True
        if e.exit_code == EXIT_CONN:
            print(f"mx: {clip(text, ERR_CAP)}", file=sys.stderr)
            return EXIT_CONN
    if a.save:
        write(a.save, text)
    if err:
        print(f"mx: ERROR {clip(text, ERR_CAP)}", file=sys.stderr)
        try:
            _, d = cached_describe(cli, toolset, sd)
            hint = param_hint(d, a.tool)
        except McpError:
            hint = ""
        if hint:
            print(f"mx: {a.tool} {hint}", file=sys.stderr)
        if a.save:
            print(f"mx: full error saved to {a.save} ({len(text)} chars)", file=sys.stderr)
        return EXIT_TOOL
    print(clip(text, a.max_chars))
    if a.save:
        print(f"[saved {len(text)} chars to {a.save}]")
    return 0


def excerpts(text, pattern, width, limit):
    """Lines matching pattern, each cut to width, total capped at limit chars."""
    rx = re.compile(pattern, re.I)
    out, used, hits = [], 0, 0
    if limit <= 0:  # --max-chars 0 means no cap
        limit = float("inf")
    if text.lstrip().startswith(("{", "[")):
        try:  # one line per JSON leaf-ish record keeps hits readable
            text = json.dumps(json.loads(text), indent=1)
        except ValueError:
            pass
    for ln in text.splitlines():
        if rx.search(ln):
            hits += 1
            piece = clip(ln.strip(), width)
            if used + len(piece) > limit:
                out.append(f"... more hits cut ({hits}+ so far); narrow --grep")
                break
            out.append(piece)
            used += len(piece) + 1
    return out or [f"(no line matches {pattern!r})"]


def tool_names(text):
    try:
        found = []

        def walk(o):
            if isinstance(o, dict):
                if isinstance(o.get("name"), str) and any(k in o for k in ("inputSchema", "parameters", "arguments", "description")):
                    found.append(o["name"])
                for v in o.values():
                    walk(v)
            elif isinstance(o, list):
                for v in o:
                    walk(v)
        walk(json.loads(text))
        return found
    except ValueError:
        return []


def cmd_describe(a, cli, sd):
    sync_cache(cli, sd)
    toolset = resolve_toolset(a.toolset, sd)
    path, text = cached_describe(cli, toolset, sd, a.refresh)
    print(f"[{toolset}: {len(text)} chars cached at {path}]")
    if a.grep:
        print("\n".join(excerpts(text, a.grep, 200, a.max_chars)))
    else:
        names = tool_names(text)
        print(clip("tools: " + ", ".join(names), a.max_chars) if names else
              "(no tool list parsed; use --grep RE, or peek --grep on the cached file)")
    return 0


def cmd_toolsets(a, cli, sd):
    sync_cache(cli, sd)
    p = os.path.join(sd, "toolsets.json")
    if a.refresh or not os.path.exists(p):
        cli.connect()
        text, err = raw_call(cli, "list_toolsets", {})
        if err:
            print(f"mx: list_toolsets failed: {clip(text, ERR_CAP)}", file=sys.stderr)
            return EXIT_TOOL
        write(p, text)
        mark_flavor(cli, sd)
    text = open(p).read()
    if a.grep:
        print("\n".join(excerpts(text, a.grep, 200, a.max_chars)))
    else:
        new = describe_flavor(cli) == "new"
        names = listed_toolsets(text, "new") if new else [n for n in names_in(text) if n.count(".") >= 2]
        print(clip(", ".join(names) or f"{len(text)} chars cached at {p}", a.max_chars))
    return 0


def cmd_save(a, cli, sd):
    if describe_flavor(cli) == "new":  # 5.9: AssetToolset only has save_asset (one path), so save all dirty via editor Python
        import step_shot
        cli = ProxyClient(cli.url, cli.timeout, sd)
        tool = step_shot.pick_python_tool(cli.list_tools())
        if not tool:
            print("mx: ERROR no Python tool found inside the editor's toolsets (5.9: enable the PythonScriptingTools plugin)")
            return EXIT_TOOL
        try:
            res = cli.call(tool["name"], step_shot.code_args(tool, SAVE_PY_59, cli))
        except McpError as e:
            print(f"mx: ERROR {clip(e, ERR_CAP)}")
            return EXIT_TOOL
        text = unwrap_return(result_text(res))
        if bool(res.get("isError")) or text.strip().lower() == "false":  # False = some package could not be saved
            print("mx: ERROR " + clip(text, ERR_CAP))
            return EXIT_TOOL
        print(clip(text, a.max_chars))
        return 0
    text, err = raw_call(cli, "call_tool", {"toolset_name": SAVE_TOOLSET, "tool_name": "save_assets",
                                      "arguments": {"asset_paths": []}})  # empty list = all dirty; the server wants the key
    print(("mx: ERROR " if err else "") + clip(text, ERR_CAP if err else a.max_chars))
    return EXIT_TOOL if err else 0


SHOT_KEYS = {"actor": "--actor", "location": "--location", "rotation": "--rotation", "verdict": "--verdict",
             "outdir": "--outdir", "width": "--width", "height": "--height", "distance": "--distance",
             "azimuth": "--azimuth", "elevation": "--elevation"}
SHOT_FLAGS = ("pie", "viewport", "editor-ui")
SHOT_HELP = """modes (pick one; no target = viewport):
  {} or {"viewport": true}   whole editor WINDOW (about 900x640) with the editor UI in it, camera untouched
  {"location":"X,Y,Z","rotation":"PITCH,YAW,ROLL"}   render from that pose (no UI, overlay may show); the viewport camera
                             is NOT moved. Example: {"location":"0,0,500","rotation":"-90,-90,0"} = top-down
  {"pie": true}              same window shot; refused if IsPIERunning says PIE is off; does NOT start PIE
                             (if the editor has no IsPIERunning tool, PIE state is reported UNCHECKED)
  {"actor": "SM_Crate"}      refused on the real editor (needs Python); find the position, use location
other keys: verdict, outdir, editor-ui, width/height (ignored on the real editor: its tools take no size,
the image is the editor's native size, and the output line says so)"""


def collect_tools(text, route, toolset):
    """Tool dicts (name + inputSchema) found in describe text; route[name] = toolset."""
    try:
        data = json.loads(text)
    except ValueError:
        return []
    found = []

    def walk(o):
        if isinstance(o, dict):
            if isinstance(o.get("name"), str) and any(k in o for k in ("inputSchema", "parameters", "arguments", "description")):
                schema = o.get("inputSchema") or o.get("parameters") or {}
                found.append({"name": o["name"], "inputSchema": schema if isinstance(schema, dict) else {}})
                route.setdefault(o["name"], toolset)
            for v in o.values():
                walk(v)
        elif isinstance(o, list):
            for v in o:
                walk(v)
    walk(data)
    return found


class ProxyClient(McpClient):
    """McpClient for the real editor: its tools sit inside toolsets behind call_tool, so list_tools() looks
    inside them (cached describes) and call() routes through call_tool. Lets step_shot work unchanged."""

    META = ("list_toolsets", "describe_toolset", "describe_toolsets", "describe_tools", "call_tool")

    def __init__(self, url, timeout, sd):
        super().__init__(url, timeout)
        self.sd, self.route = sd, {}

    def flavor(self):
        return describe_flavor(self)

    def list_tools(self):
        top = super().list_tools()
        if any(t.get("name") not in self.META for t in top):
            return top  # a server that lists its tools directly
        sync_cache(self, self.sd)
        p = os.path.join(self.sd, "toolsets.json")
        if not os.path.exists(p):
            text, err = raw_call(self, "list_toolsets", {})
            if err:
                raise McpError(f"list_toolsets failed: {clip(text, ERR_CAP)}", EXIT_TOOL)
            write(p, text)
            mark_flavor(self, self.sd)
        tools = []
        for ts in listed_toolsets(open(p).read(), describe_flavor(self)):  # includes short forms like UMGToolSet.UMGToolSet
            bad = os.path.join(self.sd, "describe", safe_name(ts) + ".fail")  # negative cache: prose tokens, etc.
            if os.path.exists(bad) and time.time() - os.path.getmtime(bad) < 600:  # not forever: the editor may
                continue                                                           # have been loading then
            try:
                _, d = cached_describe(self, ts, self.sd)
            except McpError as e:
                if e.exit_code != EXIT_CONN:  # editor unreachable is not the name's fault
                    write(bad, str(e)[:ERR_CAP])
                continue
            tools += collect_tools(d, self.route, ts)  # all toolsets: step_shot may need tools from two of them
        return tools

    def call(self, tool, args=None):
        if tool not in self.route:
            return super().call(tool, args)
        # describe lists tools as "Toolset.Tool"; call_tool adds the toolset itself, so send the bare name
        # (sending "Toolset.Tool" made the editor look for "Toolset.Toolset.Tool").
        self.connect()
        res = self.request("tools/call", {"name": "call_tool", "arguments": {
            "toolset_name": self.route[tool], "tool_name": tool.rsplit(".", 1)[-1], "arguments": args or {}}})
        if res.get("isError"):
            raise McpError(f"tool {tool} failed: {clip(result_text(res), ERR_CAP)}")
        # keep image items: Screenshot / CaptureViewport may return the PNG as image content
        return {"content": res.get("content") or [{"type": "text", "text": result_text(res)}]}


def cmd_shot(a, cli, sd):
    try:
        opts = json.loads(a.args)
        if not isinstance(opts, dict):
            raise ValueError("must be an object")
    except ValueError as e:
        print(f"mx: bad JSON options: {e}", file=sys.stderr)
        return 2
    argv = ["--label", a.label]
    for k, v in opts.items():
        if k in SHOT_FLAGS:
            if v:
                argv.append("--" + k)
        elif k in SHOT_KEYS:
            argv += [SHOT_KEYS[k], str(v)]
        else:
            print(f"mx: unknown shot option {k!r}; allowed: {sorted(list(SHOT_KEYS) + list(SHOT_FLAGS))}", file=sys.stderr)
            return 2
    if a.outdir:
        argv += ["--outdir", a.outdir]  # after the JSON keys: the flag wins
    if a.url:
        argv += ["--url", a.url]
    import step_shot  # sits next to mx.py

    def have_tool(tools):
        return bool(step_shot.pick_python_tool(tools) or step_shot.pick_shot_tool(tools)
                    or step_shot.pick_capture_tool(tools))
    # Look inside the toolsets first, so a miss is reported in toolset terms (step_shot's own message talks
    # about the top-level tools/list, which is always just the three meta tools on the real editor).
    probe = ProxyClient(cli.url, cli.timeout, sd)
    tools = probe.list_tools()
    if not have_tool(tools):
        print(f"mx: no screenshot or Python tool found inside the editor's toolsets ({len(tools)} tools seen). "
              f"Run `mx.py toolsets` and `mx.py describe TOOLSET --grep screenshot|python` to look for one.", file=sys.stderr)
        return EXIT_CONN
    orig_make_client = step_shot.make_client
    step_shot.make_client = lambda url, timeout: ProxyClient(url, timeout, sd)  # same route as standalone step_shot
    try:
        return step_shot.main(argv)
    finally:
        step_shot.make_client = orig_make_client  # do not leave the patch behind for later callers/tests


def cmd_py(a, cli, sd):
    """Run Python in the editor through whichever Python tool the toolsets offer (string arg or 5.9 CodeBlock)."""
    import step_shot  # sits next to mx.py
    script = sys.stdin.read() if a.script == "-" else a.script
    cli = ProxyClient(cli.url, cli.timeout, sd)
    tool = step_shot.pick_python_tool(cli.list_tools())
    if not tool:
        print("mx: no Python tool found inside the editor's toolsets (5.9: enable the PythonScriptingTools plugin)", file=sys.stderr)
        return EXIT_TOOL
    try:
        res = cli.call(tool["name"], step_shot.code_args(tool, script, cli))
    except McpError as e:
        print(f"mx: ERROR {clip(e, ERR_CAP)}", file=sys.stderr)
        return EXIT_TOOL
    print(clip(unwrap_return(result_text(res)), a.max_chars))
    return 0


def unwrap_return(text):
    """5.9's execute_python answers {"returnValue": X}; print X itself (a string bare, anything else as JSON).
    Any other reply (5.8.4 text, extra keys, not JSON) is printed unchanged."""
    try:
        d = json.loads(text)
    except (TypeError, ValueError):
        return text
    if isinstance(d, dict) and list(d) == ["returnValue"]:
        v = d["returnValue"]
        return v if isinstance(v, str) else json.dumps(v)
    return text


def main(argv=None):
    p = argparse.ArgumentParser(prog="mx.py", description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--url", default=None, help="MCP endpoint (default http://127.0.0.1:8010/mcp or MEGAJAM_MCP_URL)")
    p.add_argument("--timeout", type=float, default=60)
    p.add_argument("--max-chars", type=int, default=800, help="cap on printed output (default 800; 0 = no cap)")
    # The same three options are accepted after the subcommand too (SUPPRESS keeps a value given before it).
    common = argparse.ArgumentParser(add_help=False)
    common.add_argument("--url", default=argparse.SUPPRESS, help=argparse.SUPPRESS)
    common.add_argument("--timeout", type=float, default=argparse.SUPPRESS, help=argparse.SUPPRESS)
    common.add_argument("--max-chars", type=int, default=argparse.SUPPRESS, help=argparse.SUPPRESS)
    sub = p.add_subparsers(dest="verb", required=True)
    _add = sub.add_parser
    sub.add_parser = lambda name, **kw: _add(name, parents=[common], **kw)
    s = sub.add_parser("shot", formatter_class=argparse.RawDescriptionHelpFormatter,
                       description="Screenshot the editor; prints the PNG path. ARGS is a JSON object of options.",
                       epilog=SHOT_HELP)
    s.add_argument("label", help="short name; the file becomes NN-<label>.png")
    s.add_argument("args", nargs="?", default="{}", help="JSON options (see modes below); {} = viewport shot")
    s.add_argument("--outdir", metavar="DIR", help="where the PNG and steps.md go (same as the JSON key)")
    c = sub.add_parser("call")
    c.add_argument("toolset")
    c.add_argument("tool")
    c.add_argument("args", nargs="?", default="{}")
    c.add_argument("--save", metavar="PATH", help="write the full result here")
    d = sub.add_parser("describe")
    d.add_argument("toolset")
    d.add_argument("--grep", metavar="RE")
    d.add_argument("--refresh", action="store_true")
    t = sub.add_parser("toolsets")
    t.add_argument("--grep", metavar="RE")
    t.add_argument("--refresh", action="store_true")
    y = sub.add_parser("py")
    y.add_argument("script", help="Python source, or - to read stdin")
    sub.add_parser("save")
    a = p.parse_args(argv)
    cli = McpClient(a.url, a.timeout)
    sd = url_state_dir(cli.url)
    fn = {"shot": cmd_shot, "call": cmd_call, "describe": cmd_describe, "toolsets": cmd_toolsets, "py": cmd_py, "save": cmd_save}[a.verb]
    try:
        return fn(a, cli, sd)
    except McpError as e:
        print(f"mx: {clip(e, ERR_CAP)}", file=sys.stderr)
        return e.exit_code


if __name__ == "__main__":
    sys.exit(main())
