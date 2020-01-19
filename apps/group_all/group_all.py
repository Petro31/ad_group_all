import appdaemon.plugins.hass.hassapi as hass
import voluptuous as vol

APP_FH = 'group_all'
APP_CLASS = 'GroupAll'

# General

CONF_MODULE = 'module'
CONF_CLASS = 'class'
CONF_DOMAINS = 'domains'
CONF_NAME = 'name'
CONF_DOMAIN = 'domain'
CONF_LOG_LEVEL = 'log_level'
CONF_TRACK_NEW_DOMAINS = 'track_new_domains'
CONF_TRACK_NEW_ENTITIES = 'track_new_entities'
CONF_FRIENDLY_NAME = 'friendly_name'
CONF_ENTITY_ID = 'entity_id'
CONF_OBJECT_ID = 'object_id'
CONF_ENTITIES = 'entities'

# known domain names

CONF_AUTOMATION = 'automation'
CONF_COVER = 'cover'
CONF_DEVICE_TRACKER = 'device_tracker'
CONF_FAN = 'fan'
CONF_LIGHT = 'light'
CONF_LOCK = 'lock'
CONF_PLANT = 'plant'
CONF_REMOTE = 'remote'
CONF_SCRIPT = 'script'
CONF_SWITCH = 'switch'
CONF_VACUUM = 'vacuum'
CONF_CALENDAR = 'calendar'
CONF_REMEMBER_THE_MILK_ACCOUNT = 'remember_the_milk_account'

# Options
OPTION_ALL = 'all'
OPTION_LEGACY = 'legacy'
OPTION_NONE = 'none'
OPTION_CONFIGURED = 'configured'

# legacy domains

CONF_LEGACY_DOMAINS = [
    CONF_AUTOMATION, CONF_COVER, CONF_DEVICE_TRACKER, CONF_FAN,
    CONF_LIGHT, CONF_LOCK, CONF_PLANT, CONF_REMOTE, CONF_SCRIPT,
    CONF_SWITCH, CONF_VACUUM, CONF_CALENDAR, CONF_REMEMBER_THE_MILK_ACCOUNT,
]

# known unique names

NAME_DEVICE_TRACKER = 'All Devices'
NAME_SWITCH = 'All Switches'
NAME_VACUUM = 'All Vacuum Cleaners'
NAME_CALENDAR = 'Calendar'

CONF_UNIQUE_FRIENDLY_NAMES = {
    CONF_DEVICE_TRACKER:NAME_DEVICE_TRACKER,
    CONF_VACUUM:NAME_VACUUM,
    CONF_CALENDAR:NAME_CALENDAR,
    CONF_SWITCH:NAME_SWITCH,
}

# log levels
ERROR = 'ERROR'
DEBUG = 'DEBUG'
INFO = 'INFO'

#Schemas

GROUP_SCHEMA = [
    vol.Any(
        str,
        {
            vol.Required(CONF_DOMAIN): str,
            vol.Optional(CONF_NAME): str,
        }
    )
]

APP_SCHEMA = vol.Schema({
    vol.Required(CONF_MODULE): APP_FH,
    vol.Required(CONF_CLASS): APP_CLASS,
    vol.Optional(CONF_DOMAINS, default=OPTION_LEGACY): vol.Any(OPTION_ALL, OPTION_LEGACY, GROUP_SCHEMA),
    vol.Optional(CONF_LOG_LEVEL, default=DEBUG): vol.Any(DEBUG, INFO),
    vol.Optional(CONF_TRACK_NEW_DOMAINS, default=OPTION_LEGACY): vol.Any(OPTION_LEGACY, OPTION_ALL, OPTION_NONE),
    vol.Optional(CONF_TRACK_NEW_ENTITIES, default=True): bool,
})

class GroupAll(hass.Hass):
    def initialize(self):
        args = APP_SCHEMA(self.args)

        # Set Lazy Logging (to not have to restart appdaemon)
        self._level = args.get(CONF_LOG_LEVEL)
        self.log(args, level=self._level)

        self._track_entities = args.get(CONF_TRACK_NEW_ENTITIES)

        # find out if there is an override list of configured domains.
        configured = args.get(CONF_DOMAINS)
        included = None

        if isinstance(configured, list):
            included = {}
            for include in configured:
                include = ConfDomain(include)
                included[include.domain] = include
            configured = OPTION_CONFIGURED

        # decide to what groups to make
        self._track = track_domains = args.get(CONF_TRACK_NEW_DOMAINS)

        self._groups = {}
        if configured == OPTION_ALL:
            # Adding all current domains that exist.
            self.add_groups(included)

        elif configured == OPTION_LEGACY:
            # Adding all legacy domains that exist.
            self.add_groups(included, CONF_LEGACY_DOMAINS)
        else:
            # Adding all configured domains that exist.
            if track_domains == OPTION_ALL:
                filter = None
            elif track_domains == OPTION_LEGACY:
                filter = CONF_LEGACY_DOMAINS
            else:
                filter = [ g.domain for g in included.values() ]
            self.add_groups(included, filter)

        # Create state listener.

        self.handle = None
        if track_domains != OPTION_NONE or self._track_entities:
            # Listener to create new everything on state changes.
            self.applog("creating listen state handle.")
            self.handle = self.listen_state(self.track_new_items)

    def add_groups(self, included=None, filtered=None):
        """ Adds a group to home assistant at startup of app."""
        for entity_id in self.get_state().keys():
            domain = self.get_domain(entity_id)
            if domain not in self._groups:
                
                # check the filtered domains
                add = True
                if filtered is not None:
                    add = domain in filtered
                # are we adding the domain?
                if add:
                    # Did we specifically configure domains?
                    if included is not None:
                        if domain in included:
                            include = included[domain]
                            self.add_tracked_domain(include.domain, include.name)
                        else:
                            self.add_tracked_domain(domain)
                    else:
                        self.add_tracked_domain(domain)

    def get_domain(self, entity_id): return entity_id.split('.')[0]

    def applog(self, msg):
        if self._track == OPTION_NONE and self._track_entities:
            tracking = CONF_ENTITY_ID
        elif self._track_entities:
            tracking = f"{self._track} {CONF_ENTITY_ID}"
        elif self._track == OPTION_NONE:
            tracking = "no"
        else:
            tracking = self._track
        self.log(f"({tracking} tracking) {msg.capitalize()}", self._level)

    def track_new_items(self, entity, attribute, old, new, kwargs):
        domain = self.get_domain(entity)
        if self._track == OPTION_ALL:
            if domain not in self._groups:
                self.add_tracked_domain(domain)

        elif self._track == OPTION_LEGACY:
            if domain not in self._groups and domain in CONF_LEGACY_DOMAINS:
                self.add_tracked_domain(domain)

        if domain in self._groups:
            group = self._groups[domain]
            if entity not in group.entities:
                self.applog(f"adding {entity} to {domain} domain.")
                group.add_entity_id(entity)
                self.call_group_set_service(group)
                
    def add_tracked_domain(self, domain, name=None):
        """ Adds a tracked domain """
        self.applog(f"adding domain {domain}.")
        group = AppGroup(domain, name)
        group.entities =  list(self.get_state(domain).keys())
        self._groups[domain] = group

        self.call_group_set_service(group)

    def call_group_set_service(self, group):
        self.applog(f"updating {group.entity_id} with {len(group.entities)} entities.")
        self.call_service('group/set', **group.service_data)

    def terminate(self):
        if self.handle is not None:
            self.log("Canceling listen state handle.", level = self._level)
            self.cancel_listen_state(self.handle)

class ConfDomain(object):
    def __init__(self, config):
        self.name = None
        if isinstance(config, str):
            self.domain = config
        elif isinstance(config, dict):
            self.domain = config.get(CONF_DOMAIN)
            self.name = config.get(CONF_NAME)

class AppGroup(object):
    def __init__(self, domain, name=None):
        """ AppDomain Object: Simple object that contains domain and friendly name"""
        # assume that this is an entity_id
        self.domain = domain

        self._entities = []

        self.name = name
        if name is None:
            self.name = CONF_UNIQUE_FRIENDLY_NAMES[domain] if domain in CONF_UNIQUE_FRIENDLY_NAMES else f'all {self.domain}s'.title()

        self._object_id = self.name.replace(" ","_").lower()

    @property
    def object_id(self):
        return self._object_id

    @property
    def entity_id(self):
        return f'group.{self.object_id}'

    @property
    def entities(self):
        return self._entities

    @entities.setter
    def entities(self, entities):
        if isinstance(entities, list):
            self._entities = entities
            #self._entities = [] # uncomment to test for adding entities on state changes.
        else:
            raise ValueError(f"could not set entity list, recieved: {entities}")

    @property
    def service_data(self):
        self._entities.sort()
        return {CONF_OBJECT_ID:self.object_id, CONF_NAME:self.name, CONF_ENTITIES:self.entities}

    def add_entity_id(self, entity_id):
        if entity_id not in self._entities:
            self._entities.append(entity_id)
