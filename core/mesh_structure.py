# This file is part of project Sverchok. It's copyrighted by the contributors
# recorded in the version control history of the file, available from
# its original location https://github.com/nortikin/sverchok/commit/master
#
# SPDX-License-Identifier: GPL3
# License-Filename: LICENSE


from dataclasses import dataclass, field
from abc import ABC, abstractmethod
from typing import List, Tuple, Optional, Union, Any

import numpy as np


class Mesh:

    def __init__(self):
        self.name: str = 'Sv mesh'
        self.materials: List[str] = []
        self.vertex_colors: np.ndarray = []
        self.material_index: int = 0

        self._verts = Verts(self)
        self._edges = Edges(self)
        self._faces = Faces(self)
        self._loops = Loops(self)

    def __repr__(self):
        return f"<SvMesh: name='{self.name}', verts={len(self.verts.co)}, edges={len(self.edges.ind)}, faces={len(self.faces.ind)}>"

    @property
    def verts(self):
        return self._verts

    @property
    def edges(self):
        return self._edges

    @property
    def faces(self):
        return self._faces

    @property
    def loops(self):
        return self._loops

    @verts.setter
    def verts(self, verts: np.ndarray):
        self._verts.co = verts

    @edges.setter
    def edges(self, edges):
        self._edges.ind = edges

    @faces.setter
    def faces(self, faces):
        self._faces.ind = faces

    @loops.setter
    def loops(self, loops):
        self._loops.ind = loops

    def sv_deep_copy(self) -> 'Mesh': ...

    def to_bmesh(self, bm) -> None:
        bm_verts = [bm.verts.new(v) for v in self.verts]
        _ = [bm.edges.new([bm_verts[i] for i in e]) for e in self.edges]
        _ = [bm.faces.new([bm_verts[i] for i in f]) for f in self.faces]

    def search_element_with_attr(self, start: str, name: str) -> 'MeshElements':
        search_order = ['loops', 'verts', 'edges', 'faces', 'mesh']
        elements = [self.loops, self.verts, self.edges, self.faces, self]
        for element in elements[search_order.index(start):]:
            attr_values = getattr(element, name, None) 
            if attr_values is not None:
                if isinstance(attr_values, np.ndarray):
                    return element
                elif attr_values:
                    return element


class Iterable(ABC):

    def __bool__(self) -> bool:
        return bool(len(self._main_attr))

    def __len__(self) -> int:
        return len(self._main_attr)

    def __iter__(self) -> 'Iterable':
        return iter(self._main_attr)

    def __getitem__(self, item):
        return self._main_attr[item]

    @property
    @abstractmethod
    def _main_attr(self): ...


@dataclass
class Verts(Iterable):
    mesh: Mesh
    co: np.ndarray = field(default_factory=list)
    vertex_colors: np.ndarray = field(default_factory=list)

    @property
    def _main_attr(self):
        return self.co


@dataclass
class Edges(Iterable):
    mesh: Mesh
    ind: list = field(default_factory=list)

    @property
    def _main_attr(self):
        return self.ind


@dataclass
class Faces(Iterable):
    mesh: Mesh
    _ind: list = field(default_factory=list)
    material_index: list = field(default_factory=list)
    vertex_colors: np.ndarray = field(default_factory=list)

    @property
    def _main_attr(self):
        return self._ind

    @property
    def ind(self):
        return self._ind

    @ind.setter
    def ind(self, faces):
        self.mesh.loops = [i for f in faces for i in f]
        self._ind = faces


@dataclass
class Loops(Iterable):
    mesh: Mesh
    ind: list = field(default_factory=list)
    uv: np.ndarray = field(default_factory=list)
    vertex_colors: np.ndarray = field(default_factory=list)

    @property
    def _main_attr(self):
        return self.ind


MeshElements = Union[Mesh, Faces, Edges, Verts, Loops]


if __name__ == '__main__':
    me = Mesh()
    me.verts = [(0, 0, 0), (1, 0, 0), (2, 0, 0), (1, 1, 0)]

    assert bool(me.verts)
    assert len(me.verts) == 4
    assert iter(me.verts)
    assert me.verts[0] == (0, 0, 0)

    me.faces = [[0, 1, 3], [1, 2, 3]]

    assert bool(me.faces)
    assert len(me.faces) == 2
    assert iter(me.faces)
    assert not bool(me.edges)
    assert bool(me.loops)
    assert len(me.loops) == 6
    assert me.faces[1] == [1, 2, 3]