# https://github.com/praashie/flatmate

import device
import midi

from .event import RECEvent
from .hooker import Hooker
from .util import Timer

DEFAULT_PORT = device.getPortNumber()

class MIDIControl:
    def __init__(self, channel, ccNumber, port=DEFAULT_PORT, name='',
            throttling=False, lazy_feedback=False, **kwargs):
        """Manage a MIDI CC controller as an object.
        Args:
            throttling: When True, feedback is delayed until OnIdle()
            **kwargs: free attributes to be assigned"""
        self.channel = channel
        self.ccNumber = ccNumber
        self.port = port
        self.name = name
        self.value = 0
        self.value_previous = 0

        self.verbose = False
        self.throttling = throttling
        self.pending_feedback_value = None
        self.last_feedback_value = None
        self.lazy_feedback = lazy_feedback

        for attr, value in kwargs.items():
            setattr(self, attr, value)

        Hooker.include(self)

    def set_callback(self, callback):
        """Set callback to be called when the control is moved.
        def callback(control, event):
            control: the calling MIDIControl instance
            event: flmidimsg that triggered this callback
        """

        self.callback = callback
        return callback

    def getLinkedRECEvent(self):
        """If assigned by the user, get the RECEvent linked to this controller"""
        eventID = device.findEventID(self.getMIDIControlID())
        if eventID != midi.MaxInt:
            return RECEvent(eventID)

    def getMIDIControlID(self):
        return midi.EncodeRemoteControlID(self.port, self.channel, self.ccNumber)

    def matchesMsgEvent(self, event):
        status, channel = (event.status & 0xF0, event.status & 0x0F)
        return status == 0xB0 and event.data1 == self.ccNumber and channel == self.channel

    def OnControlChange(self, event):
        """Handler for FL events"""
        self.value_previous = self.value
        if self.matchesMsgEvent(event):
            self.updateValueFromEvent(event)
            if self.verbose:
                displayName = self.name or 'MidiControl({}, {})'.format(self.channel, hex(self.ccNumber))
                print('{} = {}'.format(displayName, self.value))
            if hasattr(self, "callback") and callable(self.callback):
                self.callback(self, event)

    def updateValueFromEvent(self, event):
        """Determine the final form of self.value"""
        self.value = event.controlVal

    def sendFeedback(self, value):
        """Send a CC value back to this control"""
        if self.lazy_feedback and value == self.last_feedback_value:
            return
        elif self.throttling:
            self.pending_feedback_value = value
        else:
            self._feedback(value)

    def _feedback(self, value):
        device.midiOutMsg((0xB0 + self.channel) + (self.ccNumber << 8) + (value << 16))
        self.last_feedback_value = value

    def OnIdle(self):
        if self.pending_feedback_value is not None:
            self._feedback(self.pending_feedback_value)
            self.pending_feedback_value = None

    # Available as a decorator!
    __call__ = set_callback

class MIDIButton(MIDIControl):
    _real_previous = 0
    double_click = False

    def __init__(self, *args, double_timeout=0.3, **kwargs):
        self.timer = Timer(double_timeout)
        self.timer.start()
        super().__init__(*args, **kwargs)

    def updateValueFromEvent(self, event):
        self.value = event.controlVal
        high_edge = (self.value > self._real_previous)
        self._real_previous = self.value
        self.double_click = False
        if high_edge:
            if not self.timer.ready():
                self.double_click = True
            else:
                self.timer.start()
