"""A fake `unreal` module with just enough editor to run apply / revert of ue_scatter_crew.py and ue_decals_road.py.

Models only what those scripts call: the open level (a path plus its actors), the dirty map packages, LoadMap (which, like
the real one, throws unsaved edits away without asking: they land in `discarded`), tagged actors, a straight +X JCRoad
spline, and an asset library. `calls` lists every mutating call in order (reads are not listed), so a test can assert
"dry changed nothing" or "no reload".
"""
import contextlib
import importlib.util
import io
import os
import sys
import types
import unittest

LEVEL = "/Game/Maps/L_Scene01"


class QuietCase(unittest.TestCase):
    """TestCase that swallows the scripts' own print() log lines."""

    def setUp(self):
        quiet = contextlib.redirect_stdout(io.StringIO())
        quiet.__enter__()
        self.addCleanup(quiet.__exit__, None, None, None)


class Name(str):
    pass


class Vector:
    def __init__(self, x=0.0, y=0.0, z=0.0):
        self.x, self.y, self.z = x, y, z

    def as_tuple(self):
        return (self.x, self.y, self.z)


class Rotator:  # Epic's Python order: roll, pitch, yaw
    def __init__(self, roll=0.0, pitch=0.0, yaw=0.0):
        self.roll, self.pitch, self.yaw = roll, pitch, yaw

    def as_tuple(self):
        return (self.roll, self.pitch, self.yaw)


class Pkg:
    def __init__(self, path):
        self.path = path

    def get_path_name(self):
        return self.path


class World:
    def __init__(self, pkg):
        self.pkg = Pkg(pkg)

    def get_outer(self):
        return self.pkg


class Comp:
    def __init__(self):
        self.props = {}

    def set_editor_property(self, name, value):
        self.props[name] = value

    def get_editor_property(self, name):
        return self.props[name]


class DecalComponent(Comp):
    material = None

    def set_decal_material(self, mi):
        self.material = mi


class StaticMeshComponent(Comp):
    mesh = None

    def set_static_mesh(self, mesh):
        self.mesh = mesh

    def set_collision_enabled(self, _v):
        pass

    def set_collision_profile_name(self, _v):
        pass

    def set_cast_shadow(self, _v):
        pass


class SplineComponent(Comp):
    """A straight road along +X, one metre = 100 uu."""

    def get_location_at_distance_along_spline(self, d, _space):
        return Vector(d, 0.0, 0.0)

    def get_right_vector_at_distance_along_spline(self, d, _space):
        return Vector(0.0, 1.0, 0.0)

    def get_direction_at_distance_along_spline(self, d, _space):
        return Vector(1.0, 0.0, 0.0)


class DecalActor:
    pass


class StaticMeshActor:
    pass


class Actor:
    def __init__(self, cls, label="", loc=None, rot=None):
        self.cls, self.label, self.loc, self.rot = cls, label, loc, rot
        self.props = {"tags": []}
        self.comps = {}
        self.static_mesh_component = None
        self.folder = None

    def get_actor_label(self):
        return self.label

    def set_actor_label(self, label):
        self.label = label

    def get_editor_property(self, name):
        return self.props[name]

    def set_editor_property(self, name, value):
        self.props[name] = value

    def set_actor_scale3d(self, _v):
        pass

    def set_folder_path(self, folder):
        self.folder = folder

    def get_component_by_class(self, cls):
        return self.comps.get(cls)

    def tags(self):
        return [str(t) for t in self.props["tags"]]


class Enum:
    def __getattr__(self, name):
        return name


class Asset:
    def __init__(self, path):
        self.path = path
        self.props = {"nanite_settings": types.SimpleNamespace(enabled=False)}

    def set_editor_property(self, name, value):
        self.props[name] = value

    def get_editor_property(self, name):
        return self.props[name]

    def get_name(self):
        return self.path.rsplit("/", 1)[-1]


def make_road():
    road = Actor("StaticMeshActor", "JCRoad")
    road.comps[SplineComponent] = SplineComponent()
    return road


class Editor:
    """state + the fake module (`.module`). levels: {package path: [actors]}."""

    def __init__(self, open_level=LEVEL, levels=None, dirty=(), load_ok=True, save_ok=True, save_asset_ok=True,
                 recompile_errors=(), existing_assets=True):
        self.open = open_level
        self.levels = levels if levels is not None else {open_level: [make_road()]}
        self.dirty = list(dirty)
        self.discarded = []
        self.load_ok, self.save_ok, self.save_asset_ok = load_ok, save_ok, save_asset_ok
        self.recompile_errors = list(recompile_errors)
        self.existing_assets = existing_assets
        self.calls = []
        self.deleted_assets = []
        self.assets = {}
        self.asset_list = ["/Game/Meshes/Props/Crew/x/StaticMeshes/%s.%s" % (n, n) for n in (
            "SM_Crew_Camera", "SM_Crew_Fresnel", "SM_Crew_DirChair", "SM_Crew_AppleBoxes", "SM_Crew_Sandbags", "SM_Crew_Extras")]
        self.asset_list.append("/Game/Meshes/Props/SM_TrafficCone.SM_TrafficCone")
        self.module = self._build()

    # -- helpers for tests --
    @property
    def actors(self):
        return self.levels[self.open]

    def tagged(self, tag):
        return [a for a in self.actors if tag in a.tags()]

    def mutations(self):
        return [c[0] for c in self.calls]

    def _build(self):
        ed = self
        u = types.ModuleType("unreal")
        u.Name, u.Vector, u.Rotator = Name, Vector, Rotator
        u.DecalActor, u.StaticMeshActor, u.SplineComponent, u.DecalComponent = DecalActor, StaticMeshActor, SplineComponent, DecalComponent
        for enum in ("TextureAddress", "TextureCompressionSettings", "MaterialDomain", "BlendMode", "DecalBlendMode",
                     "MaterialProperty", "CollisionEnabled", "SplineCoordinateSpace"):
            setattr(u, enum, Enum())
        for cls in ("UnrealEditorSubsystem", "Material", "MaterialFactoryNew", "MaterialExpressionTextureSampleParameter2D",
                    "MaterialExpressionConstant", "MaterialInstanceConstant", "MaterialInstanceConstantFactoryNew"):
            setattr(u, cls, type(cls, (), {}))

        class UnrealEditorSubsystem:
            def get_editor_world(self):
                return World(ed.open)

        u.UnrealEditorSubsystem = UnrealEditorSubsystem
        subs = {UnrealEditorSubsystem: UnrealEditorSubsystem()}

        def get_editor_subsystem(cls):
            return subs[cls]  # KeyError for anything the scripts should not need

        u.get_editor_subsystem = get_editor_subsystem

        class EditorLoadingAndSavingUtils:
            @staticmethod
            def load_map(path):
                ed.calls.append(("load_map", path))
                if not ed.load_ok or path not in ed.levels:
                    return None
                ed.discarded += ed.dirty  # the real LoadMap does not prompt: unsaved edits are gone
                ed.dirty = []
                ed.open = path
                return World(path)

            @staticmethod
            def save_current_level():
                ed.calls.append(("save_current_level", ed.open))
                if ed.save_ok:
                    ed.dirty = []
                return ed.save_ok

            @staticmethod
            def get_dirty_map_packages():
                return [Pkg(p) for p in ed.dirty]

        u.EditorLoadingAndSavingUtils = EditorLoadingAndSavingUtils

        class EditorLevelLibrary:
            @staticmethod
            def get_all_level_actors():
                return list(ed.actors)

            @staticmethod
            def spawn_actor_from_class(cls, loc, rot):
                ed.calls.append(("spawn", cls.__name__))
                actor = Actor(cls.__name__, "", loc, rot)
                if cls is DecalActor:
                    actor.comps[DecalComponent] = DecalComponent()
                else:
                    actor.static_mesh_component = StaticMeshComponent()
                ed.actors.append(actor)
                return actor

            @staticmethod
            def destroy_actor(actor):
                ed.calls.append(("destroy", actor.label))
                ed.actors.remove(actor)
                return True

        u.EditorLevelLibrary = EditorLevelLibrary

        class EditorAssetLibrary:
            @staticmethod
            def does_asset_exist(path):
                return ed.existing_assets or path in ed.assets

            @staticmethod
            def load_asset(path):
                return ed.assets.setdefault(path, Asset(path))

            @staticmethod
            def save_loaded_asset(obj):
                ed.calls.append(("save_asset", obj.path))
                return ed.save_asset_ok

            @staticmethod
            def list_assets(_path, recursive=True, include_folder=False):
                return list(ed.asset_list)

            @staticmethod
            def delete_asset(path):
                ed.calls.append(("delete_asset", path))
                ed.deleted_assets.append(path)
                ed.assets.pop(path, None)
                return True

        u.EditorAssetLibrary = EditorAssetLibrary

        class AssetTools:
            def create_asset(self, name, folder, _cls, _factory):
                ed.calls.append(("create_asset", "%s/%s" % (folder, name)))
                return ed.assets.setdefault("%s/%s" % (folder, name), Asset("%s/%s" % (folder, name)))

        class AssetToolsHelpers:
            @staticmethod
            def get_asset_tools():
                return AssetTools()

        u.AssetToolsHelpers = AssetToolsHelpers

        class MaterialEditingLibrary:
            @staticmethod
            def create_material_expression(_mat, _cls, _x, _y):
                return Asset("expr")

            @staticmethod
            def connect_material_property(*_a):
                return True

            @staticmethod
            def recompile_material(_mat):
                ed.calls.append(("recompile_material",))
                return list(ed.recompile_errors)

            @staticmethod
            def set_material_instance_parent(*_a):
                pass

            @staticmethod
            def set_material_instance_texture_parameter_value(*_a):
                pass

        u.MaterialEditingLibrary = MaterialEditingLibrary
        return u


def load_script(rel, name, editor, mode_env, mode="dry"):
    """Import a scripts/*.py file with `editor.module` as `unreal`. The scripts run main() at import when unreal imports,
    so the mode env var is set (default dry) for the import and restored after."""
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    spec = importlib.util.spec_from_file_location(name, os.path.join(root, rel))
    mod = importlib.util.module_from_spec(spec)
    old_mod, old_mode = sys.modules.get("unreal"), os.environ.get(mode_env)
    sys.modules["unreal"] = editor.module
    os.environ[mode_env] = mode
    try:
        spec.loader.exec_module(mod)
    finally:
        if old_mod is None:
            del sys.modules["unreal"]
        else:
            sys.modules["unreal"] = old_mod
        if old_mode is None:
            del os.environ[mode_env]
        else:
            os.environ[mode_env] = old_mode
    return mod
