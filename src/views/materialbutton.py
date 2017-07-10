#
# Transmission Line Simulator
# 
# Author(s): Jiacong Xu
# Created: Jul-6-2017
#

from materialwidget import MaterialWidget
from rippleview import RippleView
from kivy.properties import *
from kivy.uix.behaviors import ButtonBehavior
from util.hoverbehavior import HoverBehavior
from kivy.animation import Animation
from util.constants import *

class MaterialButton(ButtonBehavior, MaterialWidget, HoverBehavior):
    """
    This is a button in material widget style.
    """

    rippleView = ObjectProperty(None)

    titleLabel = ObjectProperty(None)

    iconLabel = ObjectProperty(None)

    title = StringProperty(None)

    icon = StringProperty(None)

    container = ObjectProperty(None)

    highlightColor = ListProperty([1, 1, 1, 0])

    def __init__(self, **kwargs):
        super(MaterialButton, self).__init__(**kwargs)

        self.onClick = []
        self._hoverAnim = None


    def changeStyle(self, style):
        """
        Changes the style of this button.

        style:  either 'raised' or 'flat'
        """
        if style == 'raised':
            self.backgroundColor = PRIMARY
            self.titleLabel.color = WHITE
            self.iconLabel.color = WHITE
            self.rippleView.rippleColor = RIPPLE_LIGHT
            self.raised = True
            self.highlightColor = 1, 1, 1, 0
        else:
            self.backgroundColor = WHITE
            self.titleLabel.color = TEXT_BLACK
            self.iconLabel.color = TEXT_BLACK
            self.rippleView.rippleColor = RIPPLE_DARK
            self.raised = False
            self.highlightColor = GRAY


    def on_enter(self):
        if self.disabled:
            return

        print 'entered'

        self._animateHover()


    def on_disabled(self, instance, value):
        super(MaterialButton, self).on_disabled(instance, value)

        self._animateHover()


    def on_leave(self):
        if self.disabled:
            return

        print 'left'

        self._animateHover()


    def _animateHover(self):
        if self._hoverAnim != None:
            self._hoverAnim.cancel(self)

        e = 8 if self.hovered else 2
        self._hoverAnim = Animation(elevation = e, d = 0.2, t = 'in_out_cubic')
        self._hoverAnim.start(self)



    def on_press(self):
        if self.disabled:
            return

        self.rippleView.ripple(self.last_touch.pos)


    def on_release(self):
        if self.disabled:
            return
        
        for e in self.onClick:
            e()
