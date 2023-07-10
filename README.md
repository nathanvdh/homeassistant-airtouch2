# Airtouch 2 integration
Now with basic support for airtouch2+ in beta/testing.

_Component to integrate with Polyaire Airtouch 2._

Utilizes [airtouch2-python](https://github.com/nathanvdh/airtouch2-python)

**This component will set up the following platforms.**

Platform | Description
-- | --
`climate` | Control temperature, mode, fan speed
`fan`     | Control zones on/off and dampers

## Installation

1. Click install.
1. In the HA UI go to "Configuration" -> "Integrations" click "+" and search for "airtouch2".
1. Enter the host address (IP) of the airtouch 2 system
1. Check homeassistant logs and open an issue if gateway id is not recognised.
