import svgwrite
import os

import openpathsampling as paths
import networkx as nx

from openpathsampling.storage.objproxy import LoaderProxy

import json
import matplotlib.pyplot as plt
import StringIO
from networkx.readwrite import json_graph

# CSS attributes
# text_anchor=align,
# alignment_baseline='middle',
# font_family=self.font_family,
# fill=color

class TreeRenderer(object):
    def __init__(self):
        self.start_x = 0
        self.start_y = 0
        self.scale_x = 24
        self.scale_y = 24
        self.scale_th = 24
        self.document = None
        self.font_baseline_shift = +0.05
        self.stroke_width = 0.05
        self.horizontal_gap = 0.05
        self.min_x = 10000
        self.min_y = 10000
        self.max_x = -10000
        self.max_y = -10000

        self.shift_x = 0
        self.shift_y = 0
        self.height = 0
        self.width = 0

        self.obj = list()
        self.margin = 0
        self.zoom = 1.0

    def __getattr__(self, item):
        if item in ['block', 'shade', 'v_connection', 'h_connection', 'label',
                    'connector', 'v_hook', 'vertical_label', 'text', 'range', 'h_range']:
            # This will delay the execution of the draw commands until
            # we know where to draw
            return self._delay(object.__getattribute__(self, 'draw_' + item))
        else:
            return object.__getattribute__(self, item)

    @staticmethod
    def _delay(func):
        def wrapper(*args, **kwargs):
            def fnc():
                return func(*args, **kwargs)

            return fnc

        return wrapper

    def add(self, obj):
        self.obj.append(obj)

    def pre(self, obj):
        self.obj.insert(0, obj)

    def _x(self, x):
        return self.start_x + self._w(x - self.shift_x)

    def _y(self, y):
        return self.start_y + self._h(y + self.shift_y)

    def _w(self, y):
        return self.scale_x * self.zoom * y

    def _h(self, y):
        return self.scale_y * self.zoom * y

    def _th(self, th):
        return self.scale_th * self.zoom * th

    def _xy(self, x, y):
        return self._x(x), self._y(y)

    def _wh(self, w, h):
        return self._w(w), self._h(h)

    def _xb(self, x, y):
        return self._x(x), self._y(y + self.font_baseline_shift)

    def _pad(self, xy, wh):
        self.min_x = min(self.min_x, xy[0], xy[0] + wh[0])
        self.min_y = min(self.min_y, xy[1], xy[1] + wh[1])
        self.max_x = max(self.max_x, xy[0] + wh[0], xy[0])
        self.max_y = max(self.max_y, xy[1] + wh[1], xy[1])

    def draw_connector(self, x, y, text="", cls=None):

        if cls is None:
            cls=list()

        cls += ['connector']

        return self.draw_block(x, y, text, False, False, True, True, cls=cls)

    def draw_block(self, x, y, text="",
                   extend_right=True, extend_left=True,
                   extend_top=False, extend_bottom=False,
                   w=1.0, cls=None):

        if cls is None:
            cls=list()

        cls += ['block']

        document = self.document
        padding = self.horizontal_gap

        self._pad(self._xy(x - 0.5, y - 0.3), self._wh(1.0 * w, 0.6))

        ret = list()

        ret.append(document.rect(
            class_= cls,
            insert=self._xy(x - 0.5 + padding, y - 0.3),
            size=self._wh(1.0 * w - 2 * padding, 0.6),
        ))
        if extend_left:
            ret.append(document.circle(
                class_= cls,
                center=self._xy(x - 0.5, y),
                r=self._w(padding)
            ))
        if extend_right:
            ret.append(document.circle(
                class_= cls,
                center=(self._xy(x + w - 0.5, y)),
                r=self._w(padding)
            ))

        classes =

        ret.append(document.text(
            class_="block",
            text=str(text)[:4],
            insert=self._xb(x + (w - 1.0) / 2.0, y)
        ))

        return ret

    @staticmethod
    def c(cls):
        return ' '.join(cls)

    def draw_range(self, x, y, w=1.0, color="blue", text="", align="middle",
                   extend_right=True, extend_left=True, cls=None):

        if cls is None:
            cls=list()

        cls += ['range']

        document = self.document
        padding = self.horizontal_gap

        self._pad(self._xy(x - 0.5, y - 0.3), self._wh(1.0 * w, 0.6))

        ret = list()

        ret.append(document.rect(
            class_=self.c(cls),
            insert=self._xy(x - 0.5 + padding, y - 0.05),
            size=self._wh(1.0 * w - 2 * padding, 0.1)
        ))

        if extend_left:
            ret.append(document.circle(
                class_=self.c(cls),
                center=self._xy(x - 0.5, y),
                r=self._w(padding)
            ))
            ret.append(document.rect(
                class_=self.c(cls),
                insert=self._xy(x - 0.5 + padding, y - 0.3),
                size=self._wh(0.1, 0.6)
            ))

        if extend_right:
            ret.append(document.circle(
                class_=self.c(cls),
                center=(self._xy(x + w - 0.5, y)),
                r=self._w(padding)
            ))
            ret.append(document.rect(
                class_=self.c(cls),
                insert=self._xy(x + w - 0.6 - padding, y - 0.3),
                size=self._wh(0.1, 0.6)
            ))

        ret.append(document.text(
            class_=self.c(cls),
            text=str(text),
            insert=self._xb(x + (w - 1.0) / 2.0, y - 0.3)
        ))

        return ret

    def draw_h_range(self, x, y, w=1.0, color="blue", text="", align="middle",
                   extend_top=True, extend_bottom=True, cls=None):

        if cls is None:
            cls=list()

        cls += ['h-range']

        document = self.document
        padding = self.horizontal_gap

        self._pad(self._xy(x - 0.5, y - 0.3), self._wh(1.0 * w, 0.6))

        ret = list()

        ret.append(document.rect(
            class_=self.c(cls),
            insert=self._xy(x, y - 0.3),
            size=self._wh(0.1, 1.0 * w - 0.4)
        ))

        if extend_top:
            ret.append(document.circle(
                class_=self.c(cls),
                center=self._xy(x, y - 0.3),
                r=self._w(padding)
            ))
            ret.append(document.rect(
                class_=self.c(cls),
                insert=self._xy(x - 0.5 + padding, y - 0.3),
                size=self._wh(1.0 - 2.0 * padding, 0.1)
            ))

        if extend_bottom:
            ret.append(document.circle(
                class_=self.c(cls),
                center=(self._xy(x, y + (w - 1.0) + 0.3)),
                r=self._w(padding)
            ))
            ret.append(document.rect(
                class_=self.c(cls),
                insert=self._xy(x - 0.5 + padding, y + (w - 1.0) + 0.3 - 0.1),
                size=self._wh(1.0 - 2.0 * padding, 0.1)
            ))

        ret.append(document.text(
            class_=self.c(cls),
            text=str(text),
            insert=self._xb(x - 0.3, y  + (w - 1.0) / 2.0)
        ))

        return ret

    def draw_text(self, x, y, text="", cls=None):

        if cls is None:
            cls=list()

        cls += ['text']

        document = self.document
        self._pad(self._xy(x - 0.5, y), self._wh(1.0, 5.0))

        ret = list()

        ret.append(document.text(
            class_=self.c(cls),
            text=str(text)[:4],
            insert=self._xb(x, y),
            transform='rotate(90deg)'
        ))

        return ret

    def draw_shade(self, x, y, w, cls=None):
        if cls is None:
            cls=list()

        cls += ['shade']

        document = self.document
        self._pad(self._xy(x - 0.5, y - 0.35), self._wh(1.0, 0.7))

        return [document.rect(
            class_=self.c(cls),
            insert=self._xy(x - 0.5, y + 0.35),
            size=self._wh(w, 0.1)
        )]

    def draw_shade_alt(self, x, y, w, cls=None):
        if cls is None:
            cls=list()

        cls += ['shade-alt']

        document = self.document

        self._pad(self._xy(x - 0.5, y - 0.35), self._wh(1.0, 0.7))

        return [document.rect(
            class_=self.c(cls),
            insert=self._xy(x - 0.5, y - 0.35),
            size=self._wh(w, 0.7),
        )]

    def draw_v_connection(self, x, y1, y2, cls=None):
        if cls is None:
            cls=list()

        cls += ['v-connection']

        document = self.document
        stroke_width = self.stroke_width
        padding = self.horizontal_gap

        self._pad(self._xy(x - 0.5 - stroke_width, y1),
                  self._wh(2 * stroke_width, y2 - y1))

        return [document.line(
            class_=self.c(cls),
            start=self._xy(x - 0.5, y1 + padding),
            end=self._xy(x - 0.5, y2 - padding)
        )]

    def draw_v_hook(self, x1, y1, x2, y2, cls=None):
        if cls is None:
            cls=list()

        cls += ['v-hook']

        document = self.document
        stroke_width = self.stroke_width
        padding = self.horizontal_gap

        self._pad(self._xy(x1 - stroke_width, y1),
                  self._wh(2 * stroke_width + x2 - x1, y2 - y1))

        return [document.line(
            class_=self.c(cls),
            start=self._xy(x1, y1 + padding + 0.3),
            end=self._xy(x2, y2 - padding - 0.3)
        )]

    def draw_h_connection(self, x1, x2, y, cls=None):
        if cls is None:
            cls=list()

        cls += ['h-connection']

        document = self.document
        stroke_width = self.stroke_width
        padding = self.horizontal_gap

        self._pad(self._xy(x1, y - stroke_width),
                  self._wh(x2 - x1, 2 * stroke_width))

        return [document.line(
            class_=self.c(cls),
            start=self._xy(x1 + 0.5 + padding, y),
            end=self._xy(x2 - 0.5, y)
        )]

    def draw_label(self, x, y, w, text, cls=None):
        if cls is None:
            cls=list()

        cls += ['label']

        document = self.document

        self._pad(
            self._xy(x, y), self._wh(w, 0.6)
        )

        return [document.text(
            class_=self.c(cls),
            text=str(text),
            insert=self._xb(x, y),
        )]

    def draw_vertical_label(self, x, y, w, text):
        if cls is None:
            cls=list()

        cls += ['v-label']

        document = self.document

        self._pad(
            self._xy(x, y),
            self._wh(w, 0.6)
        )

        return [document.text(
            text=str(text),
            insert=(0,0),
            transform='translate(' +
                ' '.join(map(str, self._xb(x, y))) +
                ')rotate(270)'
        )]



    def to_document(self):

        self.start_x = self.margin
        self.start_y = self.margin

        self.document = svgwrite.Drawing()
        self.document['width'] = str(self._width()) + 'px'
        self.document['height'] = str(self._height()) + 'px'
        self.document['class'] = 'opstree'

        for obj in self.obj:
            parts = obj()
            map(self.document.add, parts)

        return self.document

    def to_svg(self):
        doc = self.to_document()
        return doc.tostring()

    def to_html(self, svg=None):
        if svg is None:
            svg = self.to_svg()

        html = '<!DOCTYPE html><html style="margin:0px; padding:0px; width:100%;">' + \
               svg + '<body style="margin:0px; padding:0px;"></body></html>'

        return html

    def _height(self):
        return self._h(self.height) + self.margin * 2

    def _width(self):
        return self._w(self.width) + self.margin * 2

    def write_html(self, file_name='tree.html'):
        with open(file_name, 'w') as f:
            f.write(self.to_html())

    def save_pdf(self, file_name='tree.pdf'):
        h = self._height()
        w = self._width()

        h_margin = 3.5
        v_margin = 3.5

        page_height = str(25.4 / 75.0 * h + v_margin) + 'mm'
        page_width = str(25.4 / 75.0 * w + h_margin) + 'mm'

        with open('tree_xxx.html', 'w') as f:
            f.write(self.to_html())

        bash_command = "wkhtmltopdf -l --page-width " + page_width + \
                      " --page-height " + page_height + \
                      " --disable-smart-shrinking " + \
                      "-B 1mm -L 1mm -R 1mm -T 1mm tree_xxx.html " + file_name

        os.system(bash_command)

    def clear(self):
        self.obj = []


class MoveTreeBuilder(object):
    def __init__(self, storage=None, op=None, states=None):
        self.rejected = False
        self.p_x = dict()
        self.p_y = dict()
        self.obj = list()
        self.storage = storage
        self.renderer = TreeRenderer()
        self.op = op
        if states is None:
            states = {}
        self.states = states

        self.t_count = 0
        self.traj_ens_x = dict()
        self.traj_ens_y = dict()

        self.traj_repl_x = dict()
        self.traj_repl_y = dict()

        self.ens_x = list()
        self.repl_x = list()

    def full(self, ensembles, clear=True):

        storage = self.storage

        if clear:
            self.renderer.clear()
        level_y = dict()

        old_sset = paths.SampleSet([])

        self.t_count = 1

        self.ens_x = [None] * len(ensembles)
        self.repl_x = [None] * len(ensembles)

        for sset in storage.samplesets[0:2]:
            path = sset.movepath
            # level_y = dict()

            for level, sub in path.depth_post_order(lambda this: tuple(
                    [this, old_sset.apply_samples(this.samples)])):
                self.t_count += 1

                sub_mp, sub_set = sub

                if sub_mp.__class__ is paths.SamplePathMoveChange:
                    self.renderer.add(
                        self.renderer.block(-8.0 + level, self.t_count, 'blue'))
                    self.renderer.add(
                        self.renderer.label(
                            -8.0 + level, self.t_count, 3,
                            sub_mp.mover.__class__.__name__[:-5],
                            align='start', color='black')
                    )
                else:
                    self.renderer.add(
                        self.renderer.block(-8.0 + level, self.t_count,
                                            'green'))
                    self.renderer.add(
                        self.renderer.label(-8.0 + level, self.t_count, 3,
                                            sub_mp.__class__.__name__[:-8],
                                            align='start', color='black')
                    )

                if level + 1 in level_y \
                        and level_y[level + 1] == self.t_count - 1:
                    self.renderer.add(
                        self.renderer.v_connection(-7.0 + level, self.t_count,
                                                   self.t_count - 1, 'black')
                    )
                    del level_y[level + 1]

                if level in level_y and level_y[level]:
                    self.renderer.add(
                        self.renderer.v_connection(-8.0 + level, self.t_count,
                                                   level_y[level], 'black')
                    )

                level_y[level] = self.t_count

                self.render_ensemble_line(ensembles, sub_set, color='gray')
                self.render_replica_line(len(ensembles), sub_set, color='gray')

            self.t_count += 1

            self.render_ensemble_line(ensembles, sset)
            self.render_replica_line(len(ensembles), sset)

            self.renderer.add(self.renderer.block(-8.0, self.t_count, 'black'))
            self.renderer.add(
                self.renderer.label(-8.0, self.t_count, 3,
                                    'storage.sampleset[%d]' % sset.idx[storage.samplesets],
                                    align='start', color='black')
            )

            old_sset = sset
            self.t_count += 1

        self.renderer.shift_x = - 9.0
        self.renderer.shift_y = -0.5
        self.renderer.height = 1.0 * self.t_count + 1.0
        self.renderer.width = 1.0 * len(ensembles) + 20.5


    def mover(self, pathmover, ensembles, clear=True):

        storage = self.storage

        if clear:
            self.renderer.clear()
        level_y = dict()

        self.t_count = 1

        self.ens_x = [None] * len(ensembles)
        self.repl_x = [None] * len(ensembles)

        path = pathmover

        self.render_ensemble_mover_head(ensembles, 5)

        self.t_count = 5

        total = len(path)

        for ens_idx, ens in enumerate(ensembles):
            self.renderer.add(
                self.renderer.v_hook( ens_idx, self.t_count, ens_idx,
                                           self.t_count + total + 1, 'gray')
            )

        for level, sub in path.depth_pre_order(lambda this: tuple(
                [this, None])):
            self.t_count += 1

            sub_mp, sub_set = sub

            name = sub_mp.name

            if sub_mp.__class__ is paths.SamplePathMoveChange:
                self.renderer.add(
                    self.renderer.block(-8.0 + level, self.t_count, 'blue'))
                self.renderer.add(
                    self.renderer.label(
                        -8.0 + level, self.t_count, 3,
                        sub_mp.mover.__class__.__name__[:-5],
                        align='start', color='black')
                )
            else:
                self.renderer.add(
                    self.renderer.block(-8.0 + level, self.t_count,
                                        'green'))
                self.renderer.add(
                    self.renderer.label(-8.0 + level, self.t_count, 3,
                                        sub_mp.__class__.__name__[:-5],
                                        align='start', color='black')
                )

            if False:
                if level + 1 in level_y \
                        and level_y[level + 1] == self.t_count - 1:
                    self.renderer.add(
                        self.renderer.v_connection(-7.0 + level, self.t_count,
                                                   self.t_count - 1, 'orange')
                    )
                    del level_y[level + 1]

                if level in level_y and level_y[level]:
                    self.renderer.add(
                        self.renderer.v_connection(-8.0 + level, self.t_count,
                                                   level_y[level], 'black')
                    )

            if True:
                if level - 1 in level_y \
                        and level_y[level - 1] == self.t_count - 1:
                    self.renderer.add(
                        self.renderer.v_connection(-8.0 + level, self.t_count,
                                                   self.t_count - 1, 'black')
                    )
                if level + 1 in level_y:
                    del level_y[level + 1]

                if level in level_y and level_y[level]:
                    self.renderer.add(
                        self.renderer.v_connection(-8.0 + level, self.t_count,
                                                   level_y[level], 'black')
                    )


            level_y[level] = self.t_count

            self.render_ensemble_mover_line(ensembles, sub_mp, color='gray')
#            self.render_replica_line(len(ensembles), sub_set, color='gray')

        self.t_count += 1

#        self.render_ensemble_line(ensembles, sset)
#        self.render_replica_line(len(ensembles), sset)

#        self.renderer.add(self.renderer.block(-8.0, self.t_count, 'black'))
#        self.renderer.add(
#            self.renderer.label(-8.0, self.t_count, 3,
#                                'storage.sampleset[%d]' % sset.idx[storage],
#                                align='start', color='black')
#        )

        self.t_count += 1

        self.renderer.shift_x = - 9.0
        self.renderer.shift_y = -0.5
        self.renderer.height = 1.0 * self.t_count + 1.0
        self.renderer.width = 1.0 * len(ensembles) + 20.5

    def render_ensemble_mover_head(self, ensembles, yp=None):
        for ens_idx, ens in enumerate(ensembles):
            txt = chr(ens_idx + 65)

            label = ens.name if hasattr(ens, 'name') else ens.__class__.__name__[:-8]

            self.renderer.add(
                self.renderer.vertical_label(
                    ens_idx, yp, 5, '[' + txt + '] ' + label,
                    align='start'
                )
            )

    def render_ensemble_mover_line(self, ensembles, mover, yp=None, color='black'):
        if yp is None:
            yp = self.t_count

        storage = self.storage
        for ens_idx, ens in enumerate(ensembles):
            txt = chr(ens_idx + 65)
            show = False
            in_ens = mover.input_ensembles
            out_ens = mover.output_ensembles
            if in_ens is None or None in in_ens or ens in in_ens:
                self.renderer.add(
                    self.renderer.connector(ens_idx, yp - 0.12, 'green', ''))

                show = True

            if out_ens is None or None in out_ens or ens in out_ens:
                self.renderer.add(
                    self.renderer.connector(ens_idx, yp + 0.12, 'red', ''))

                show = True

            if show:
                self.renderer.add(
                    self.renderer.block(ens_idx, yp, 'rgb(200,200,200)', txt))


#        for ens_idx, ens in enumerate(ensembles):
#            samp_ens = [samp for samp in sset if samp.ensemble is ens]
#            if len(samp_ens) > 0:
#                traj_idx = samp_ens[0].trajectory.idx[storage]
#                self.ens_x[ens_idx] = traj_idx
#                self.traj_ens_x[traj_idx] = ens_idx
#                self.traj_ens_y[traj_idx] = self.t_count

    def render_ensemble_line(self, ensembles, sset, yp=None, color='black'):
        if yp is None:
            yp = self.t_count

        storage = self.storage
        for ens_idx, ens in enumerate(ensembles):
            samp_ens = [samp for samp in sset if samp.ensemble is ens]
            if len(samp_ens) > 0:
                traj_idx = samp_ens[0].trajectory.idx[storage.trajectories]
                txt = str(traj_idx)
                if len(samp_ens) > 1:
                    txt += '+'

                my_color = color

                if traj_idx in self.ens_x:
                    self.renderer.add(
                        self.renderer.v_hook(self.traj_ens_x[traj_idx],
                                             self.traj_ens_y[traj_idx], ens_idx,
                                             self.t_count, 'black'))
                    if self.traj_ens_x[traj_idx] != ens_idx:
                        my_color = 'red'
                else:
                    if len(self.ens_x) > 0:
                        my_color = 'red'

                if my_color != 'gray':
                    self.renderer.add(
                        self.renderer.connector(ens_idx, yp, my_color, txt))

        for ens_idx, ens in enumerate(ensembles):
            samp_ens = [samp for samp in sset if samp.ensemble is ens]
            if len(samp_ens) > 0:
                traj_idx = samp_ens[0].trajectory.idx[storage.trajectories]
                self.ens_x[ens_idx] = traj_idx
                self.traj_ens_x[traj_idx] = ens_idx
                self.traj_ens_y[traj_idx] = self.t_count

    def render_replica_line(self, replica, sset, yp=None, color='black'):
        if yp is None:
            yp = self.t_count

        storage = self.storage
        for repl_idx in range(0, replica):
            samp_repl = [samp for samp in sset if samp.replica == repl_idx - 1]
            xp = repl_idx + 10
            if len(samp_repl) > 0:
                traj_idx = samp_repl[0].trajectory.idx[storage.trajectories]
                txt = str(traj_idx)
                if len(samp_repl) > 1:
                    txt += '+'
                my_color = color
                if traj_idx in self.repl_x:
                    self.renderer.add(
                        self.renderer.v_hook(self.traj_repl_x[traj_idx],
                                             self.traj_repl_y[traj_idx], xp,
                                             self.t_count, 'black'))
                    if self.traj_repl_x[traj_idx] != xp:
                        my_color = 'red'
                else:
                    if len(self.repl_x) > 0:
                        my_color = 'red'

                if my_color != 'gray':
                    self.renderer.add(
                        self.renderer.connector(xp, yp, my_color, txt))

        for repl_idx in range(replica):
            samp_repl = [samp for samp in sset if samp.replica == repl_idx - 1]
            xp = repl_idx + 10
            if len(samp_repl) > 0:
                traj_idx = samp_repl[0].trajectory.idx[storage.trajectories]
                self.repl_x[repl_idx] = traj_idx
                self.traj_repl_x[traj_idx] = xp
                self.traj_repl_y[traj_idx] = self.t_count

    @staticmethod
    def _get_min_max(d):
        return min(d.values()), max(d.values())


class PathTreeBuilder(object):
    def __init__(self, storage, op=None, states=None):
        self.rejected = False
        self.p_x = dict()
        self.p_y = dict()
        self.obj = list()
        self.storage = storage
        self.renderer = TreeRenderer()
        self.op = op
        self.show_redundant = False
        if states is None:
            states = []
        self.states = states

    @staticmethod
    def construct_heritage(sample):
        list_of_samples = []

        samp = sample

        while samp.parent is not None:
            # just one sample so use this
            list_of_samples.append(samp)
            samp = samp.parent

        # reverse to get origin first
        return [samp for samp in reversed(list_of_samples)]

    def from_samples(self, samples, clear=True):

        options = {
            paths.ReplicaExchangeMover: {
                'name': 'RepEx',
                'overlap': 'line',
                'fw': 'blocks',
                'bw': 'blocks',
                'all': 'hidden',
                'overlap_label': 'RepEx',
                'suffix': 'x',
                'label_position': 'bw'
            },
            'ui': {
                'trajectory': True,
                'step': True,
                'correlation': True,
                'sample': True
            },
            'settings': {
                'register_rejected': False
            }
        }

        if len(samples) == 0:
            # no samples, nothing to do
            # TODO: Raise an exception or just ignore and don't output anything?
            return

        p_x = dict()
        p_y = dict()

        if clear:
            self.renderer.clear()

        t_count = 1
        shift = 0

        for sample in samples:
            draw_okay = False
            line_okay = False
            direction = 0
            mover_type = type(sample.mover)
            traj = sample.trajectory

            

            # get connection to existing
            pos_first = p_x.get(traj[0])
            pos_last = p_x.get(traj[-1])

            new_shift = shift
            overlap_reversed = False

            index_bw = None

            for snap_idx in range(len(traj)):
                snap = traj[snap_idx]
                if snap in p_x:
                    connect_bw = p_x[snap]
                    index_bw = snap_idx
                    shift_bw = connect_bw - snap_idx
                    break

            if index_bw is None:
                # no overlap, so skip
                first = False
                color = 'black'
                draw_okay = True
                shift = 0
            else:
                for snap_idx in range(len(traj) - 1, -1, -1):
                    snap = traj[snap_idx]
                    if snap in p_x:
                        connect_fw = p_x[snap]
                        index_fw = snap_idx
                        shift_fw = connect_fw - snap_idx
                        break

                # now we know that the overlap is between (including) [connect_bw, connect_fw]
                # and the trajectory looks like [bw, ...] + [old, ...] + [fw, ...]
                # with bw
                # [0, ..., index_bw -1] + [index_bw, ..., index_fw] + [index_fw + 1, ..., len(traj) - 1]
                # both shift_fw and shift_bw always exist and are the same if the trajectory is extended
                # or truncated or shoot from. If the overlapping trajectory is reversed before extending
                # then we get
                # [0, ..., index_fw -1] + [index_fw, ..., index_bw] + [index_bw + 1, ..., len(traj) - 1]
                # this can be checked by index_bw > index_fw or shift_fw != shift_bw

                new_shift = (shift_bw + shift_fw) / 2

                if index_bw > index_fw:
                    index_bw, index_fw = index_fw, index_bw
                    overlap_reversed = True

            if mover_type in options:
                view_options = options[mover_type]

                # Reversal

                traj_str = str(self.storage.idx(sample.trajectory)) + view_options['suffix']

                if view_options['label_position'] == 'bw':
                    self.renderer.add(
                        self.renderer.label(shift, t_count, 1, traj_str)
                    )
                elif view_options['label_position'] == 'fw':
                    self.renderer.add(
                        self.renderer.label(shift + len(traj), t_count, 1, traj_str)
                    )

                if view_options['overlap'] == 'line':
                    self.renderer.add(
                        self.renderer.range(new_shift + index_bw, t_count, new_shift + index_fw - index_bw,
                                            view_options['name'], cls=['overlap'] )
                    )

                if view_options['bw'] == 'line':
                    self.renderer.add(
                        self.renderer.range(new_shift + 0, t_count, new_shift + index_bw, cls=['fw'])
                    )

                if view_options['fw'] == 'line':
                    self.renderer.add(
                        self.renderer.range(new_shift + 0, t_count, new_shift + index_bw, cls=['bw'])
                    )

                for pos, snapshot in enumerate(sample.trajectory):
                    conf = snapshot
                    conf_idx = self.storage.idx(conf)
                    if not conf_idx in p_y:

                        p_x[conf_idx] = shift + pos
                        p_y[conf_idx] = t_count

                        pos_x = p_x[conf_idx]
                        pos_y = p_y[conf_idx]

                        txt = ''

                        if self.op is not None:
                            txt = self.op(snapshot)

                        self.renderer.add(
                            self.renderer.block(
                                pos_x,
                                pos_y,
                                color,
                                txt,
                                extend_left = pos > 0,
                                extend_right = pos < len(sample.trajectory) - 1
                            ))

            if line_okay:
                for pos, snapshot in enumerate(sample.trajectory):
                    conf = snapshot
                    conf_idx = self.storage.idx(conf)
                    p_x[conf_idx] = shift + pos
                    p_y[conf_idx] = t_count

            t_count += 1

        self.p_x = p_x
        self.p_y = p_y

        min_x, max_x = self._get_min_max(self.p_x)
        min_y, max_y = self._get_min_max(self.p_y)

        self.renderer.shift_x = min_x - 8.5
        self.renderer.shift_y = 0
        self.renderer.height = max_y - min_y + 5.0
        self.renderer.width = max_x - min_x + 10.0

        matrix = self._to_matrix()

        if hasattr(self, 'states') and len(self.states) > 0:
            for color, op in self.states:
                xp = None
                for y in range(0, max_y - min_y + 1):
                    left = None
                    yp = y + min_y
                    for x in range(0, (max_x - min_x + 1)):
                        xp = x + min_x

                        # if matrix[y][x] is not None:
                        #     self.renderer.pre(
                        #         self.renderer.shade(xp, yp, 0.9,
                        #                             'black')
                        #     )


                        if matrix[y][x] is not None\
                            and bool(op(LoaderProxy(self.storage.snapshots, matrix[y][x]))):
                                if left is None:
                                    left = xp
                        else:
                            if left is not None:
                                self.renderer.pre(
                                    self.renderer.shade(left, yp, xp - left,
                                                        color)
                                )
                                left = None

                    if left is not None:
                        self.renderer.pre(
                            self.renderer.shade(left, yp, xp - left + 1, color)
                        )

        prev = samples[0].trajectory
        old_tc = 1
        trial_list = {}
        for step in self.storage.steps:
            for ch in step.change:
                if ch.samples is not None:
                    for trial in ch.samples:
                        trial_list[trial] = step.mccycle

        for tc, s in enumerate(samples):
            if tc > 0 and not paths.Trajectory.is_correlated(s.trajectory, prev):
                self.renderer.add(
                    self.renderer.h_range(self.renderer.shift_x + 5.5, old_tc - 0.1, 1 + tc - old_tc + 0.2, 'black', "" ))


                old_tc = 1 + tc

                prev = s.trajectory

            self.renderer.add(
                self.renderer.label(self.renderer.shift_x + 5.0, 1 + tc, 1, str(
                    self.storage.idx(s)) , align='end',
                                    color=font_color)
            )

            if s in trial_list:
                txt = str(trial_list[s])
            else:
                txt = '---'

            self.renderer.add(
                self.renderer.label(self.renderer.shift_x + 2.0, 1 + tc, 1, str(
                    txt) , align='end',
                                    color=font_color)
            )

        self.renderer.add(
            self.renderer.h_range(self.renderer.shift_x + 2.0, 0.9, len(samples) + 0.2, 'black', "" ))

        self.renderer.add(
            self.renderer.h_range(self.renderer.shift_x + 5.5, old_tc - 0.1, 1 + len(samples) - old_tc + 0.2, 'black', "", extend_bottom=False))


    def _get_min_max(self, d):
        return min(d.values()), max(d.values())

    def _to_matrix(self):
        min_x, max_x = self._get_min_max(self.p_x)
        min_y, max_y = self._get_min_max(self.p_y)

        matrix = [[None] * (max_x - min_x + 1) for n in
                  range(max_y - min_y + 1)]

        for s in self.p_x:
            px = self.p_x[s]
            py = self.p_y[s]
            matrix[py - min_y][px - min_x] = s

        return matrix


class SVGDiGraph(nx.DiGraph):
  def _repr_svg_(self):
     plt.ioff() # turn off interactive mode
     fig=plt.figure(figsize=(2,2))
     ax = fig.add_subplot(111)
     nx.draw_shell(self, ax=ax)
     output = StringIO.StringIO()
     fig.savefig(output,format='svg')
     plt.ion() # turn on interactive mode
     return output.getvalue()

class MoveTreeNX(object):
    """Class to create a networkX based representation of a pathmover and change

    """
    def __init__(self, pathmover):
        self.pathmover = pathmover
        self._G = None

    @property
    def _enumeration(self):
        return enumerate(self.pathmover.depth_post_order(lambda this: this))

    @property
    def G(self):
        if self._G is None:
            G = nx.DiGraph()

            node_list = dict()

            for idx, data in self._enumeration:
                level, node = data
                node_list[node] = idx
                G.add_node(idx, name=node.name)

            for idx, data in self._enumeration:
                level, node = data
                subnodes = node.submovers
                for subnode in subnodes:
                    G.add_edge(node_list[node], node_list[subnode])

            self._G = G

        return self._G

    def draw(self):
        G = self.G
        pos = nx.spring_layout(G)

        for idx, data in self._enumeration:
            level, node = data
            nx.draw_networkx_nodes(
                G,
                pos,
                nodelist=[idx],
                node_color='r',
                node_size=500,
                alpha=0.8
            )

        plt.axis('off')
        plt.show()

        return G

    @property
    def json_tree(self):
        data = json_graph.tree_data(self.G,len(self.G)-1)
        return json.dumps(data)

    @property
    def json_node_link(self):
        data = json_graph.node_link_data(self.G)
        return json.dumps(data)

    def d3vis(self):
        return '''
        <style>

        .node circle {
          fill: #fff;
          stroke: steelblue;
          stroke-width: 1.5px;
        }

        .node {
          font: 10px sans-serif;
          stroke: black;
          stroke-width:0.35px;
        }

        .link {
          fill: none;
          stroke: #ccc;
          stroke-width: 1.5px;
        }

        </style>
        <div><svg id="d3-circ-tree-svg"></svg></div>
        ''' + '<script>var graph = ' + self.json_tree + ';</script>' + \
        '''
        <script src="http://d3js.org/d3.v3.min.js"></script>

        <script>

//        require.config({paths: {d3: "http://d3js.org/d3.v3.min"}});

//        require(["d3"], function(d3) {
        (function() {
            var diameter = 1200;
            var padding = 0;

            var tree = d3.layout.tree()
                .size([360, diameter / 2 - 120])
                .separation(function(a, b) { return (a.parent == b.parent ? 1 : 2) / a.depth; });

            var nodes = tree.nodes(graph),
                links = tree.links(nodes);

            var diagonal = d3.svg.diagonal.radial()
                .projection(function(d) { return [d.y, d.x / 360 * Math.PI]; });

            var vertical = d3.svg.diagonal.radial()
                .projection(function(d) { return [-d.x, -d.y / 360 * Math.PI]; });

            var svg = d3.select("#d3-circ-tree-svg")
                .attr("width", (diameter + padding))
                .attr("height", (diameter + padding) / 2)
              .append("g")
                .attr("transform", "translate(" + (diameter + padding) / 2 + "," + (0*(diameter + padding) / 2 + 50) + ")rotate(90)");

            var link = svg.selectAll(".link")
              .data(links)
              .enter().append("path")
              .attr("class", "link")
              .attr("d", diagonal);

            link.append("circle")
              .attr("r", 4.5);

            var node = svg.selectAll(".node")
              .data(nodes)
            .enter().append("g")
              .attr("class", "node")
              .attr("transform", function(d) { return "rotate(" + (d.x / 2 - 90) + ")translate(" + d.y + ")"; })

            node.append("circle")
              .attr("r", 4.5);

            node.append("text")
              .attr("dy", ".31em")
              .attr("text-anchor", function(d) { return d.x < 180 ? "start" : "end"; })
              .attr("transform", function(d) { return d.x < 180 ? "translate(8)" : "rotate(180)translate(-8)"; })
              .text(function(d) { return d.name; });

            d3.select(self.frameElement).style("height", diameter + 50 + "px");
//        });
        })();

        </script>
        '''

class ReplicaHistoryTree(PathTreeBuilder):
    """
    Simplified PathTreeBuilder for the common case of tracking a replica
    over some steps.

    Intended behaviors: 
    * The samples are determined during initialization.
    * The defaults are as similar to the old tree representation as
      reasonable.
    * This object also calculates decorrelated trajectories (which is
      usually what we look for from this tree). The number of decorrelated
      trajectories is obtained as the length of that list, and does not
      require an extra method.
    """
    def __init__(self, storage, steps, replica):
        # TODO: if we implement substorages (see #330) we can remove the
        # steps variable here and just iterate over storage.
        super(ReplicaHistoryTree, self).__init__(storage)
        self.replica = replica
        self.steps = steps
        self._accepted_samples = None
        self._trial_samples = None

        # defaults:
        self.rejected = False 
        self.show_redundant = False
        self.states = []

        # build the tree 
        self.from_samples(self.samples)
        self.view = self.renderer

    def rebuild(self):
        """Rebuild the internal structures.

        It seems like some changes in the visualization require a complete
        rebuild. That's not ideal. If that can be changed, this function
        could be removed.
        """
        self.from_samples(self.samples)


    @property
    def accepted_samples(self):
        """
        Returns the accepted samples in self.steps involving self.replica
        """
        if self._accepted_samples is None:
            samp = self.steps[-1].active[self.replica]
            samples = [samp]
            while samp.parent is not None:
                samp = samp.parent
                samples.append(samp)
            
            self._accepted_samples = list(reversed(samples))

        return self._accepted_samples
 
    @property
    def trial_samples(self):
        """
        Returns trial samples from self.steps involving self.replica
        """
        if self._trial_samples is None:
            samp = self.steps[0].active[self.replica]
            samples = [samp]
            for step in self.steps:
                rep_trials = [s for s in step.change.trials 
                              if s.replica==self.replica]
                if len(rep_trials) > 0:
                    samples.append(rep_trials[-1])

            self._trial_samples = samples

        return self._trial_samples

    @property
    def samples(self):
        if self.rejected:
            return self.trial_samples
        else:
            return self.accepted_samples

    @property
    def decorrelated_trajectories(self):
        """List of decorrelated trajectories from the internal samples.

        In path sampling, two trajectories are said to be "decorrelated" if
        they share no frames in common. This is particularly important in
        one-way shooting. This function returns the list of trajectories,
        making the number (i.e., the length of the list) also easily
        accessible.
        """
        prev = self.samples[0].trajectory
        decorrelated = [prev]
        # TODO: this should be restricted to accepted samples
        for s in [samp for samp in self.samples]:
            if not paths.Trajectory.is_correlated(s.trajectory, prev):
                decorrelated.append(s.trajectory)
                prev = s.trajectory

        return decorrelated
    
