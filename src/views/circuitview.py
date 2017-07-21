#
# Transmission Line Simulator
# 
# Author(s): Jiacong Xu
# Created: Jul-9-2017
#

from kivy.uix.widget import Widget
from materialwidget import MaterialWidget
from materialtextfield import MaterialTextField
from kivy.properties import *
from models.resistor import Resistor
from models.oscilloscope import Oscilloscope
from util.constants import *
from util.hoverbehavior import HoverBehavior
from kivy.core.window import Window
from contextmenu import ContextMenu
from models.circuit import Circuit
from loadeditor import LoadEditor
from wireeditor import WireEditor
from sourceeditor import SourceEditor
from oscilloscopeeditor import OscilloscopeEditor
from kivy.metrics import *

class CircuitWidget(Widget, HoverBehavior):
    """
    Base widget for circuit element, supporting functions like highlighting,
    editing hooks and right click menu hooks.
    """
    def __init__(self, **kwargs):
        super(CircuitWidget, self).__init__(**kwargs)

        self.contextMenuLayer = None
        self.element = None
        self.updateCircuit = None
        self._menuPos = 0
        self.wireScale = 0
        self.menu = None
        self.prev = None
        self.next = None


    def on_touch_down(self, touch):
        if self.collide_point(touch.pos[0], touch.pos[1]):
            self._menuPos = touch.pos

            if touch.button == 'left':
                self.on_left_click(touch.pos)
            elif touch.button == 'right':
                self.on_right_click(touch.pos)

            return True

        return super(CircuitWidget, self).on_touch_down(touch)


    def on_left_click(self, pos):
        self.onEditClicked()


    def on_right_click(self, pos):
        if self.menu == None:
            return

        if self.menu.parent != None:
            self.menu.dismiss(False)
        
        self.menu.show(self.contextMenuLayer, pos, True)


    def onEditClicked(self):
        self.popup.updateCircuit = self.updateCircuit

        if self.popup.parent != None:
            self.popup.dismiss(False)
        
        self.popup.show(self.contextMenuLayer, self._menuPos, True)
        self.popup.updateValues()


    def onNext(self):
        """
        Opens the next menu
        """
        self.popup.dismiss(False)
        self.next._menuPos = self.next.center
        self.next.onEditClicked()


    def onPrev(self):
        """
        Opens the next menu
        """
        self.popup.dismiss(False)
        self.prev._menuPos = self.prev.center
        self.prev.onEditClicked()


class Wire(CircuitWidget):
    """
    This renders a wire.
    """
    def __init__(self, wireModel, **kwargs):
        super(Wire, self).__init__(**kwargs)

        self.element = wireModel
        titles = ['Edit Wire', 'Split Wire', 'Add Oscilloscope']
        actions = [self.onEditClicked, self.onSplitClicked, self.onAddOscilloscopeClicked]

        if self._canDelete():
            titles.append('Delete Wire')
            actions.append(self.onDeleteClicked)

        self.menu = ContextMenu(titles, actions)
        self.popup = WireEditor(self.element)
        self.popup.onPrev = self.onPrev
        self.popup.onNext = self.onNext


    def _canDelete(self):
        return self.element.prev.prev != None or self.element.next.next != None


    def onSplitClicked(self):
        """
        Splits the wire at the menu pos, cutting it in two identical halves.
        """
        wirePos = (self._menuPos[0] - self.x) / self.wireScale
        # Discretize the above.
        self.splitWire(self.element, wirePos)


    def onAddOscilloscopeClicked(self):
        wirePos = (self._menuPos[0] - self.x) / self.wireScale + self.element.position
        self.addOscilloscope(wirePos)


    def onDeleteClicked(self):
        self.deleteWire(self.element)


class Load(CircuitWidget):
    """
    This renders a load.
    """
    def __init__(self, loadModel, **kwargs):
        super(Load, self).__init__(**kwargs)

        titles = ['Edit Load', 'Reset Circuit']
        actions = [self.onEditClicked, self.onResetClicked]
        self.menu = ContextMenu(titles, actions)
        self.element = loadModel
        self.popup = popup = LoadEditor(self.element)
        self.popup.onPrev = self.onPrev


    def onResetClicked(self):
        self.resetCircuit()


class Source(CircuitWidget):
    """
    This renders a power source.
    """
    def __init__(self, element, **kwargs):
        super(Source, self).__init__(**kwargs)

        titles = ['Edit Source', 'Reset Circuit']
        actions = [self.onEditClicked, self.onResetClicked]
        self.menu = ContextMenu(titles, actions)
        self.element = element
        self.popup = SourceEditor(self.element)
        self.popup.onNext = self.onNext


    def onResetClicked(self):
        self.resetCircuit()


class Oscilloscope(CircuitWidget):
    """
    This renders an oscilloscope. Oscilloscopes may only be placed on the bottom
    wire.
    """
    def __init__(self, element, **kwargs):
        super(Oscilloscope, self).__init__(**kwargs)

        titles = ['Edit Oscilloscope', 'Delete Oscilloscope']
        actions = [self.onEditClicked, self.onDeleteClicked]
        self.menu = ContextMenu(titles, actions)
        self.element = element
        self.popup = OscilloscopeEditor(self.element)
        self.popup.onPrev = self.onPrev
        self.popup.onNext = self.onNext


    def onDeleteClicked(self):
        self.deleteOscilloscope(self.element)



class CircuitView(MaterialWidget):
    """
    This is dedicated in displaying and editing the circuit.

    model:  the simulation model.
    """

    _begin = ListProperty([0, 0])
    _end = ListProperty([0, 0])

    model = ObjectProperty(None)

    contextMenuLayer = ObjectProperty(None)


    def __init__(self, **kwargs):
        """
        Initializes the view without drawing anything.
        """
        super(CircuitView, self).__init__(**kwargs)

        self.oscilloscopeViews = []
    

    def on_model(self, *args, **kwargs):
        self.rebuildCircuit()


    def setGraphBounds(self, box):
        """
        This takes the graph positions and aligns itself with the graph.

        box:    a bounding box in the format of [x, y, width, height]
        """
        bx, by = box[0], self.y + self.height * 0.2
        ex, ey = box[0] + box[2], self.y + self.height * 0.8

        if abs(bx - self._begin[0]) < 1e-7 and \
            abs(by - self._begin[1]) < 1e-7 and \
            abs(ex - self._end[0]) < 1e-7 and \
            abs(ey - self._end[1]) < 1e-7:
            return

        self._begin = bx, by
        self._end = ex, ey
        self.rebuildCircuit()


    def resetCircuit(self):
        self.model.reset()
        self.model.circuit = Circuit()


    def updateCircuit(self):
        """
        Updates the length of all the wires in the diagram and also positioning
        of oscilloscopes.
        """
        scale = (self._end[0] - self._begin[0]) / self.model.circuit.getLength()
        lastX = 0

        for c in self.children:
            if type(c) == Wire:
                c.x = float(self._begin[0] + c.element.position * scale + WIRE_THICKNESS)
                c.width = float(max(0, c.element.length * scale - 2 * WIRE_THICKNESS))
                lastX = c.x + c.element.position

        self.repositionOscilloscopes()


    def rebuildCircuit(self):
        """
        Removes all circuit elements from the diagram and add everything from
        model.
        """
        if self.model == None:
            return

        self.clear_widgets()

        # Add a source.
        source = Source(self.model.circuit.head)
        source.contextMenuLayer = self.contextMenuLayer
        source.resetCircuit = self.resetCircuit
        source.size = self.height / 8, self.height / 8
        source.center = float(self._begin[0]), float((self._begin[1] + self._end[1]) / 2)
        self.add_widget(source)

        # Add each wire and oscilloscpe with a connector inbetween.
        e = self.model.circuit.head.next
        scale = (self._end[0] - self._begin[0]) / self.model.circuit.getLength()
        c = None

        p1 = source
        p2 = source

        while e.next != None:
            # This element is either a wire or oscilloscope.
            if type(e) == Resistor:
                p1, p2 = self._addWireView(e, p1, p2)

            # Proceed to the next element
            e = e.next

        # Add a load.
        load = Load(e)
        load.contextMenuLayer = self.contextMenuLayer
        load.resetCircuit = self.resetCircuit
        load.size = self.height / 18, self.height / 6
        load.center = float(self._end[0]), float((self._begin[1] + self._end[1]) / 2)
        load.prev = p1
        p1.next = load
        p2.next = load
        self.add_widget(load)

        # Oscilloscopes
        self.oscilloscopeViews = []
        h = self.model.circuit.headOscilloscope

        while h != None:
            self._addOscilloscopeView(h)
            h = h.next


    def addOscilloscope(self, pos):
        """
        Adds an oscilloscope at given circuit position, and creates the view.
        """
        o = self.model.circuit.insertOscilloscope(pos)
        self._addOscilloscopeView(o)
        

    def _addOscilloscopeView(self, oscilloscope):
        scale = (self._end[0] - self._begin[0]) / self.model.circuit.getLength()
        ov = Oscilloscope(oscilloscope)
        ov.contextMenuLayer = self.contextMenuLayer
        ov.size = float(self.height / 12), float(self.height / 4)
        ov.pos = float(self._begin[0] + oscilloscope.position * scale), self._begin[1]
        ov.deleteOscilloscope = self.deleteOscilloscope
        self.add_widget(ov)

        # Link views
        for i in self.oscilloscopeViews:
            if oscilloscope.prev != None and i.element == oscilloscope.prev:
                i.next = ov
                ov.prev = i

            if oscilloscope.next != None and i.element == oscilloscope.next:
                i.prev = ov
                ov.next = i

        self.oscilloscopeViews.append(ov)


    def _addWireView(self, wire, p1, p2):
        scale = (self._end[0] - self._begin[0]) / self.model.circuit.getLength()

        w1 = Wire(wire)
        w1.wireScale = scale
        w1.updateCircuit = self.updateCircuit
        w1.addOscilloscope = self.addOscilloscope
        w1.deleteWire = self.deleteWire
        w1.splitWire = self.splitWire
        w1.contextMenuLayer = self.contextMenuLayer
        w1.x = float(self._begin[0] + wire.position * scale + WIRE_THICKNESS)
        w1.width = float(max(0, wire.length * scale - 2 * WIRE_THICKNESS))
        w1.height = 2 * WIRE_THICKNESS + 48
        w1.center_y = self._begin[1]

        w1.prev = p1
        w1.prev.next = w1

        self.add_widget(w1)

        w2 = Wire(wire)
        w2.wireScale = scale
        w2.updateCircuit = self.updateCircuit
        w2.addOscilloscope = self.addOscilloscope
        w2.deleteWire = self.deleteWire
        w2.splitWire = self.splitWire
        w2.contextMenuLayer = self.contextMenuLayer
        w2.x = float(self._begin[0] + wire.position * scale + WIRE_THICKNESS)
        w2.width = float(max(0, wire.length * scale - 2 * WIRE_THICKNESS))
        w2.height = 2 * WIRE_THICKNESS + 48
        w2.center_y = self._end[1]

        w2.prev = p2
        w2.prev.next = w2

        self.add_widget(w2)

        return w1, w2



    def deleteOscilloscope(self, element):
        """
        Removes the given oscilloscope from the model and the view.
        """
        # Removes from model.
        if element.prev == None and element.next == None:
            self.model.circuit.headOscilloscope = None

        if element.prev != None:
            element.prev.next = element.next

        if element.next != None:
            element.next.prev = element.prev

        # Removes from view.
        for i in self.oscilloscopeViews:
            if i.element == element:
                if i.prev != None:
                    i.prev.next = i.next

                if i.next != None:
                    i.next.prev = i.prev

                self.remove_widget(i)

                break


    def splitWire(self, element, pos):
        """
        Splits the wire at the given position.
        """
        copy = Resistor(element.resistance)
        copy.length = element.length - pos
        copy.next = element.next
        element.length = pos
        element.next = copy
        self.rebuildCircuit()



    def deleteWire(self, element):
        """
        Removes the given wire from the model and the view.
        """
        element.prev.next = element.next

        # Delete any oscilloscopes on this segment, and also changes positioning
        # for later oscilloscopes.
        h = self.model.circuit.headOscilloscope

        while h != None:
            if h.position > element.position:
                if h.position < element.position + element.length:
                    # Delete oscilloscope.
                    if h.prev != None:
                        h.prev.next = h.next

                    if h.next != None:
                        h.next.prev = h.prev

                    if h.prev == None and h.next == None:
                        self.model.circuit.headOscilloscope = None
                else:
                    # Move oscilloscope.
                    h.position -= element.length

            h = h.next

        self.rebuildCircuit()


    def repositionOscilloscopes(self):
        """
        Moves all oscilloscopes to their correct positions on screen.
        """
        scale = (self._end[0] - self._begin[0]) / self.model.circuit.getLength()

        for ov in self.oscilloscopeViews:
            ov.size = float(self.height / 12), float(self.height / 4)
            ov.x = float(self._begin[0] + ov.element.position * scale)
