# Home Assistant Add Domain Group (group.all_`<domain>`s)

[![hacs_badge](https://img.shields.io/badge/HACS-Default-orange.svg?style=for-the-badge)](https://github.com/custom-components/hacs)
<br><a href="https://www.buymeacoffee.com/Petro31" target="_blank"><img src="https://cdn.buymeacoffee.com/buttons/default-black.png" width="150px" height="35px" alt="Buy Me A Coffee" style="height: 35px !important;width: 150px !important;" ></a>

_Group All app for AppDaemon._

Adds a domain group to Home Assistant.  The added domain groups will have the name group.all_`<domain>`s.  e.g. if the domain light is specified, group.all_lights will be created.

With the `legacy` configuration, this will restore all hidden `group.all_*` groups that were removed in Home Assitant v0.104:

* group.all_automations
* group.all_covers
* group.all_devices
* group.all_fans
* group.all_lights
* group.all_locks
* group.all_plants
* group.all_remotes
* group.all_scripts
* group.all_switches
* group.all_vacuum_cleaners
* group.calendar
* group.remember_the_milk_accounts

## Installation

Download the `group_all` directory from inside the `apps` directory here to your local `apps` directory, then add the configuration to enable the `hacs` module.

## Example App configuration

#### Legacy Configuration
```yaml
# Creates all legacy groups.  All newly created entity_id's will be added to the correct legacy group.
events:
  module: group_all
  class: GroupAll
```

#### Only all switches
```yaml
# Creates group.all_switches, the group will update when a new switch is added to home assistant.
events:
  module: group_all
  class: GroupAll
  track_new_domains = none
  domains:
  - switch
```

#### Advanced
```yaml
# Creates groups for all domains.
# Renames group.all_switches to group.switch_master
# Renames group.all_lights to group.light_master
# Any new entity_id that is created will be added to the correct group.
events:
  module: group_all
  class: GroupAll
  track_new_domains: all
  track_new_entities: true
  domains:
  - domain: switch
    name: Switch Master
  - domain: light
    name: Light Master
  log_level: INFO
```

#### App Configuration
key | optional | type | default | description
-- | -- | -- | -- | --
`module` | False | string | group_all | The module name of the app.
`class` | False | string | GroupAll | The name of the Class.
`track_new_domains` | True | `'all'` &#124; `'legacy'` &#124; `'none'` | `'legacy'` | Dynamically adds new domains without user intervention.  `'all'` will add all new domains. `'legacy'` will add all new legacy domains. `'none'` will turn this off.
`track_new_entities` | True | bool | `true` | Dynamically adds new entity_id's to the entity list of a domain group.
`domains` | True | `'all'` &#124; `'legacy'` &#124; list | `'legacy'` | A list of domain names or domain objects.  `'all'` will create all available domains at startup.  `'legacy'` will create all avialable legacy domains.  Adding your own list will only create those domain groups.  If `'track_new_domains'` is set to `'all'` or `'legacy'`, these settings will only override the group friendly name.  
`log_level` | True | `'INFO'` &#124; `'DEBUG'` | `'INFO'` | Switches log level.

#### Domain Object Configuration
key | optional | type | default | description
-- | -- | -- | -- | --
`domain` | False | string | | The domain name.
`name` | True | string | | Friendly Name of the created group.
