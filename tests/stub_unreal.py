"""A tiny fake `unreal` module so the in-editor script text in force_save_level.py can really run."""
import contextlib
import io
import sys
import types


class Pkg:
    def __init__(self, path):
        self.path = path

    def get_path_name(self):
        return self.path

    def mark_package_dirty(self):
        pass


class Actor:
    def __init__(self, label, has_external_api=True, external=False):
        self.label, self.external = label, external
        if has_external_api:
            self.is_package_external = lambda: self.external

    def get_actor_label(self):
        return self.label

    def get_package(self):
        return Pkg("/Game/__ExternalActors__/Maps/L_Main/" + self.label)


class World:
    def __init__(self, pkg, actors):
        self.pkg, self.actors = Pkg(pkg), actors

    def get_outer(self):
        return self.pkg


def make(state):
    """state: 'world', optional 'new_level_ok' / 'load_level_ok' (default True), 'levels' {pkg: actors}."""
    u = types.ModuleType("unreal")

    class LevelEditorSubsystem:
        def new_level(self, path):
            if state.get("new_level_ok", True):
                state["world"] = World(path, [])
                return True
            return False

        def load_level(self, pkg):
            if not state.get("load_level_ok", True):
                return False
            if state["world"].pkg.path != pkg:
                state["world"] = World(pkg, list(state["levels"][pkg]))
            return True

        def save_current_level(self):
            return True

    class UnrealEditorSubsystem:
        def get_editor_world(self):
            return state["world"]

    class EditorActorSubsystem:
        def get_all_level_actors(self):
            return list(state["world"].actors)

    subs = {c: c() for c in (LevelEditorSubsystem, UnrealEditorSubsystem, EditorActorSubsystem)}
    u.LevelEditorSubsystem, u.UnrealEditorSubsystem, u.EditorActorSubsystem = list(subs)
    u.get_editor_subsystem = lambda cls: subs[cls]

    class Paths:
        convert_relative_path_to_full = staticmethod(lambda p: "/proj/" + p)
        file_exists = staticmethod(lambda p: False)
        combine = staticmethod(lambda parts: "/".join(parts))
        project_content_dir = staticmethod(lambda: "Content")

    class PackageName:
        long_package_name_to_filename = staticmethod(lambda pkg, ext: "Content" + pkg[len("/Game"):] + ext)

    u.Paths = Paths
    if not state.get("no_package_name"):  # UE 5.9 Python has no unreal.PackageName
        u.PackageName = PackageName
    return u


def run(script, state):
    sys.modules["unreal"] = make(state)
    out = io.StringIO()
    try:
        with contextlib.redirect_stdout(out):
            exec(compile(script, "<editor>", "exec"), {"__name__": "__editor__"})
    finally:
        del sys.modules["unreal"]
    return out.getvalue()
