"""Base code for presentation elements."""

from __future__ import annotations

from typing import TYPE_CHECKING, Callable, Generic, List, Optional, TypeVar

from gaphas.state import observed, reversible_method

from gaphor.core.modeling import Element
from gaphor.core.modeling.event import DiagramItemDeleted
from gaphor.core.modeling.properties import association, relation_one

if TYPE_CHECKING:
    from gaphas.canvas import Canvas  # noqa
    from gaphas.connector import Handle  # noqa
    from gaphas.matrix import Matrix  # noqa

S = TypeVar("S", bound=Element)


class Presentation(Element, Generic[S]):
    """This presentation is used to link the behaviors of
    `gaphor.core.modeling` and `gaphas.Item`.

    Note that Presentations are not managed by the Element Factory.
    Instead, Presentation objects are owned by Diagram. As a result they
    do not emit ElementCreated and ElementDeleted events. Presentations
    have their own create and delete events: DiagramItemCreated and
    DiagramItemDeleted.
    """

    def __init__(self, id=None, model=None):
        super().__init__(id, model)

        self._canvas: Optional[Canvas] = None

        def update(event):
            if self.canvas:
                self.canvas.request_update(self)

        self._watcher = self.watcher(default_handler=update)

        self.watch("subject")

    subject: relation_one[S] = association(
        "subject", Element, upper=1, opposite="presentation"
    )

    handles: Callable[[Presentation], List[Handle]]

    matrix: Matrix

    @observed
    def _set_canvas(self, canvas):
        """Set the canvas.

        Should only be called from Canvas.add and Canvas.remove().
        """
        assert not canvas or not self._canvas or self._canvas is canvas
        if self._canvas:
            self.teardown_canvas()
        self._canvas = canvas
        if canvas:
            self.setup_canvas()

    reversible_method(
        _set_canvas, _set_canvas, bind={"canvas": lambda self, canvas: self._canvas}
    )

    def setup_canvas(self):
        """Called when the canvas is set for the item.

        This method can be used to create constraints.
        """
        pass

    def teardown_canvas(self):
        """Called when the canvas is unset for the item.

        This method can be used to dispose constraints.
        """
        pass

    canvas = property(lambda s: s._canvas, _set_canvas)

    def request_update(self, matrix=True):
        if self.canvas:
            self.canvas.request_update(self, matrix=matrix)

    @property
    def diagram(self):
        canvas = self.canvas
        return canvas.diagram if canvas else None

    def watch(self, path, handler=None):
        """Watch a certain path of elements starting with the DiagramItem. The
        handler is optional and will default to a simple self.request_update().

        Watches should be set in the constructor, so they can be registered
        and unregistered in one shot.

        This interface is fluent(returns self).
        """
        self._watcher.watch(path, handler)
        return self

    def subscribe_all(self):
        """Subscribe all watched paths, as defined through `watch()`."""
        self._watcher.subscribe_all()

    def unsubscribe_all(self):
        """Unsubscribe all watched paths, as defined through `watch()`."""
        self._watcher.unsubscribe_all()

    def unlink(self):
        """Remove the item from the canvas and set subject to None."""
        if self.canvas:
            diagram = self.diagram
            self.canvas.remove(self)
            super().unlink()
            self.handle(DiagramItemDeleted(diagram, self))


Element.presentation = association(
    "presentation", Presentation, composite=True, opposite="subject"
)
