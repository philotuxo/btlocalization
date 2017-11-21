import dbus
import sys
import signal


def getAdapters():

    BUS_NAME = 'org.bluez'
    SERVICE_NAME = 'org.bluez'
    ADAPTER_INTERFACE = SERVICE_NAME + '.Adapter1'

    bus = dbus.SystemBus()
    manager = dbus.Interface(bus.get_object(BUS_NAME, '/'),
                             'org.freedesktop.DBus.ObjectManager')

    objects =  manager.GetManagedObjects()

    adapters = []

    for path, interfaces in objects.iteritems():
        adapter = interfaces.get(ADAPTER_INTERFACE)
        if adapter is None:
            continue
        adapters.append(
            (str(adapter.get(u'Address')), str(adapter.get(u'Alias')))
        )
    return adapters

def signal_handler(signal, frame):
        print('You pressed Ctrl+C!')
        sys.exit(0)

