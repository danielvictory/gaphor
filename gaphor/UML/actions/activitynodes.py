"""Activity control nodes."""

import ast
import math

from gaphas.constraint import constraint
from gaphas.geometry import Rectangle, distance_line_point
from gaphas.item import Handle, Item, LinePort
from gaphas.state import observed, reversible_property
from gaphas.util import path_ellipse

from gaphor import UML
from gaphor.core.modeling import Presentation
from gaphor.diagram.presentation import ElementPresentation, Named
from gaphor.diagram.shapes import Box, EditableText, IconBox, Text, stroke
from gaphor.diagram.support import represents
from gaphor.UML.modelfactory import stereotypes_str

DEFAULT_JOIN_SPEC = "and"


def no_movable_handles(item):
    for h in item._handles:
        h.movable = False


class ActivityNodeItem(Named):
    """Basic class for simple activity nodes.

    Simple activity node is not resizable.
    """


@represents(UML.InitialNode)
class InitialNodeItem(ElementPresentation, ActivityNodeItem):
    """Representation of initial node.

    Initial node has name which is put near top-left side of node.
    """

    def __init__(self, connections, id=None, model=None):
        super().__init__(connections, id, model)
        no_movable_handles(self)

        self.shape = IconBox(
            Box(style={"min-width": 20, "min-height": 20}, draw=draw_initial_node),
            # Text should be left-top
            Text(
                text=lambda: stereotypes_str(self.subject),
            ),
            EditableText(text=lambda: self.subject and self.subject.name or ""),
        )

        self.watch("subject[NamedElement].name")
        self.watch("subject.appliedStereotype.classifier.name")


def draw_initial_node(_box, context, _bounding_box):
    cr = context.cairo
    stroke = context.style["color"]
    if stroke:
        cr.set_source_rgba(*stroke)

    r = 10
    d = r * 2
    path_ellipse(cr, r, r, d, d)
    cr.set_line_width(0.01)
    cr.fill()


@represents(UML.ActivityFinalNode)
class ActivityFinalNodeItem(ElementPresentation, ActivityNodeItem):
    """Representation of activity final node.

    Activity final node has name which is put near right-bottom side of
    node.
    """

    def __init__(self, connections, id=None, model=None):
        super().__init__(connections, id, model)
        no_movable_handles(self)

        self.shape = IconBox(
            Box(
                style={"min-width": 30, "min-height": 30}, draw=draw_activity_final_node
            ),
            # Text should be right-bottom
            Text(
                text=lambda: stereotypes_str(self.subject),
            ),
            EditableText(text=lambda: self.subject and self.subject.name or ""),
        )

        self.watch("subject[NamedElement].name")
        self.watch("subject.appliedStereotype.classifier.name")


def draw_activity_final_node(_box, context, _bounding_box):
    cr = context.cairo
    stroke_color = context.style["color"]
    if stroke_color:
        cr.set_source_rgba(*stroke_color)

    inner_radius = 10
    outer_radius = 15
    r = outer_radius + 1

    d = r * 2
    path_ellipse(cr, r, r, d, d)
    cr.set_line_width(0.01)
    cr.set_line_width(2)
    stroke(context)

    d = inner_radius * 2
    path_ellipse(cr, r, r, d, d)
    cr.set_line_width(0.01)
    cr.fill()


@represents(UML.FlowFinalNode)
class FlowFinalNodeItem(ElementPresentation, ActivityNodeItem):
    """Representation of flow final node.

    Flow final node has name which is put near right-bottom side of
    node.
    """

    def __init__(self, connections, id=None, model=None):
        super().__init__(connections, id, model)
        no_movable_handles(self)

        self.shape = IconBox(
            Box(style={"min-width": 20, "min-height": 20}, draw=draw_flow_final_node),
            # Text should be right-bottom
            Text(
                text=lambda: stereotypes_str(self.subject),
            ),
            EditableText(text=lambda: self.subject and self.subject.name or ""),
        )

        self.watch("subject[NamedElement].name")
        self.watch("subject.appliedStereotype.classifier.name")


def draw_flow_final_node(_box, context, _bounding_box):
    cr = context.cairo
    r = 10
    d = r * 2
    path_ellipse(cr, r, r, d, d)
    stroke(context)

    dr = (1 - math.sin(math.pi / 4)) * r
    cr.move_to(dr, dr)
    cr.line_to(d - dr, d - dr)
    cr.move_to(dr, d - dr)
    cr.line_to(d - dr, dr)
    stroke(context, fill=False)


@represents(UML.DecisionNode)
class DecisionNodeItem(ElementPresentation, ActivityNodeItem):
    """Representation of decision or merge node."""

    def __init__(self, connections, id=None, model=None):
        super().__init__(connections, id, model)
        no_movable_handles(self)

        self._combined = None

        self.shape = IconBox(
            Box(style={"min-width": 20, "min-height": 30}, draw=draw_decision_node),
            # Text should be left-top
            Text(
                text=lambda: stereotypes_str(self.subject),
            ),
            EditableText(text=lambda: self.subject and self.subject.name or ""),
        )

        self.watch("subject[NamedElement].name")
        self.watch("subject.appliedStereotype.classifier.name")

    def save(self, save_func):
        if self._combined:
            save_func("combined", self._combined)
        super().save(save_func)

    def load(self, name, value):
        if name == "combined":
            self._combined = value
        else:
            super().load(name, value)

    @observed
    def _set_combined(self, value):
        self._combined = value

    combined = reversible_property(lambda s: s._combined, _set_combined)


def draw_decision_node(_box, context, _bounding_box):
    """Draw diamond shape, which represents decision and merge nodes."""
    cr = context.cairo
    r = 15
    r2 = r * 2 / 3

    cr.move_to(r2, 0)
    cr.line_to(r2 * 2, r)
    cr.line_to(r2, r * 2)
    cr.line_to(0, r)
    cr.close_path()
    stroke(context)


@represents(UML.ForkNode)
class ForkNodeItem(Item, Presentation[UML.ForkNode], Named):
    """Representation of fork and join node."""

    def __init__(self, connections, id=None, model=None):
        super().__init__(id=id, model=model)
        self._connections = connections

        h1, h2 = Handle(), Handle()
        self._handles.append(h1)
        self._handles.append(h2)
        self._ports.append(LinePort(h1.pos, h2.pos))

        self._combined = None

        self.shape = IconBox(
            Box(style={"min-width": 0, "min-height": 45}, draw=self.draw_fork_node),
            Text(
                text=lambda: stereotypes_str(self.subject),
            ),
            EditableText(text=lambda: self.subject and self.subject.name or ""),
            Text(
                text=lambda: isinstance(self.subject, UML.JoinNode)
                and self.subject.joinSpec not in (None, DEFAULT_JOIN_SPEC)
                and f"{{ joinSpec = {self.subject.joinSpec} }}"
                or "",
            ),
        )

        self.watch("subject[NamedElement].name")
        self.watch("subject.appliedStereotype.classifier.name")
        self.watch("subject[JoinNode].joinSpec")

        connections.add_constraint(self, constraint(vertical=(h1.pos, h2.pos)))
        connections.add_constraint(self, constraint(above=(h1.pos, h2.pos), delta=30))

    def save(self, save_func):
        save_func("matrix", tuple(self.matrix))
        save_func("height", float(self._handles[1].pos.y))
        if self._combined:
            save_func("combined", self._combined)
        super().save(save_func)

    def load(self, name, value):
        if name == "matrix":
            self.matrix.set(*ast.literal_eval(value))
        elif name == "height":
            self._handles[1].pos.y = ast.literal_eval(value)
        elif name == "combined":
            self._combined = value
        else:
            # DiagramItem.load(self, name, value)
            super().load(name, value)

    @observed
    def _set_combined(self, value):
        # self.preserve_property('combined')
        self._combined = value

    combined = reversible_property(lambda s: s._combined, _set_combined)

    def draw(self, context):
        h1, h2 = self.handles()
        height = h2.pos.y - h1.pos.y
        self.shape.draw(context, Rectangle(0, 0, 1, height))

    def draw_fork_node(self, _box, context, _bounding_box):
        """
        Draw vertical line - symbol of fork and join nodes. Join
        specification is also drawn above the item.
        """
        cr = context.cairo

        cr.set_line_width(6)
        h1, h2 = self._handles
        cr.move_to(h1.pos.x, h1.pos.y)
        cr.line_to(h2.pos.x, h2.pos.y)

        stroke(context)

    def point(self, pos):
        h1, h2 = self._handles
        d, p = distance_line_point(h1.pos, h2.pos, pos)
        # Subtract line_width / 2
        return d - 3
