import esphome.codegen as cg
import esphome.config_validation as cv
from esphome import automation
from esphome.components import climate, sensor
from esphome.const import CONF_AWAY_CONFIG, CONF_COOL_ACTION, CONF_DEFAULT_TARGET_TEMPERATURE, \
    CONF_DEFAULT_TARGET_TEMPERATURE_HIGH, CONF_DEFAULT_TARGET_TEMPERATURE_LOW, CONF_HEAT_ACTION, \
    CONF_ID, CONF_IDLE_ACTION, CONF_SENSOR, CONF_HYSTERESIS

bang_bang_ns = cg.esphome_ns.namespace('bang_bang')
BangBangClimate = bang_bang_ns.class_('BangBangClimate', climate.Climate, cg.Component)
BangBangClimateTargetTempConfig = bang_bang_ns.struct('BangBangClimateTargetTempConfig')


def validate_target_temperature(supports_cool, supports_heat, has_hysteresis):
    has_two_point_target_temperature = (not has_hysteresis) or (supports_heat and supports_cool)

    def validate(obj):
        if has_two_point_target_temperature:
            if ((CONF_DEFAULT_TARGET_TEMPERATURE_LOW not in obj)
                    or (CONF_DEFAULT_TARGET_TEMPERATURE_HIGH not in obj)):
                raise cv.Invalid("{} and {} are required.".format(
                    CONF_DEFAULT_TARGET_TEMPERATURE_LOW, CONF_DEFAULT_TARGET_TEMPERATURE_HIGH))
            if CONF_DEFAULT_TARGET_TEMPERATURE in obj:
                raise cv.Invalid("{} is not allowed in two point target temperature configuration."
                                 .format(CONF_DEFAULT_TARGET_TEMPERATURE))
        else:
            if CONF_DEFAULT_TARGET_TEMPERATURE_LOW in obj:
                raise cv.Invalid("{} is not allowed, use {}.".format(
                    CONF_DEFAULT_TARGET_TEMPERATURE_LOW, CONF_DEFAULT_TARGET_TEMPERATURE))
            if CONF_DEFAULT_TARGET_TEMPERATURE_HIGH in obj:
                raise cv.Invalid("{} is not allowed, use {}.".format(
                    CONF_DEFAULT_TARGET_TEMPERATURE_HIGH, CONF_DEFAULT_TARGET_TEMPERATURE))
            if CONF_DEFAULT_TARGET_TEMPERATURE not in obj:
                raise cv.Invalid("{} is required.".format(CONF_DEFAULT_TARGET_TEMPERATURE))
            if supports_heat:
                obj[CONF_DEFAULT_TARGET_TEMPERATURE_LOW] = obj[CONF_DEFAULT_TARGET_TEMPERATURE]
            if supports_cool:
                obj[CONF_DEFAULT_TARGET_TEMPERATURE_HIGH] = obj[CONF_DEFAULT_TARGET_TEMPERATURE]
            del obj[CONF_DEFAULT_TARGET_TEMPERATURE]
        return obj

    return validate


def validate_two_point_target_temperature(value):
    supports_cool = CONF_COOL_ACTION in value
    supports_heat = CONF_HEAT_ACTION in value
    has_hysteresis = CONF_HYSTERESIS in value
    validate = validate_target_temperature(supports_cool, supports_heat, has_hysteresis)
    if CONF_AWAY_CONFIG in value:
        value[CONF_AWAY_CONFIG] = validate(value[CONF_AWAY_CONFIG])
    return validate(value)


CONFIG_SCHEMA = cv.All(climate.CLIMATE_SCHEMA.extend({
    cv.GenerateID(): cv.declare_id(BangBangClimate),
    cv.Required(CONF_SENSOR): cv.use_id(sensor.Sensor),
    cv.Optional(CONF_DEFAULT_TARGET_TEMPERATURE): cv.temperature,
    cv.Optional(CONF_DEFAULT_TARGET_TEMPERATURE_LOW): cv.temperature,
    cv.Optional(CONF_DEFAULT_TARGET_TEMPERATURE_HIGH): cv.temperature,
    cv.Required(CONF_IDLE_ACTION): automation.validate_automation(single=True),
    cv.Optional(CONF_COOL_ACTION): automation.validate_automation(single=True),
    cv.Optional(CONF_HEAT_ACTION): automation.validate_automation(single=True),
    cv.Optional(CONF_AWAY_CONFIG): cv.Schema({
        cv.Optional(CONF_DEFAULT_TARGET_TEMPERATURE): cv.temperature,
        cv.Optional(CONF_DEFAULT_TARGET_TEMPERATURE_LOW): cv.temperature,
        cv.Optional(CONF_DEFAULT_TARGET_TEMPERATURE_HIGH): cv.temperature,
    }),
    cv.Optional(CONF_HYSTERESIS): cv.temperature,
}).extend(cv.COMPONENT_SCHEMA), cv.has_at_least_one_key(CONF_COOL_ACTION, CONF_HEAT_ACTION),
                       validate_two_point_target_temperature)


def to_code(config):
    var = cg.new_Pvariable(config[CONF_ID])
    yield cg.register_component(var, config)
    yield climate.register_climate(var, config)

    sens = yield cg.get_variable(config[CONF_SENSOR])
    cg.add(var.set_sensor(sens))

    normal_config = BangBangClimateTargetTempConfig(
        config.get(CONF_DEFAULT_TARGET_TEMPERATURE_LOW, cg.NAN),
        config.get(CONF_DEFAULT_TARGET_TEMPERATURE_HIGH, cg.NAN)
    )
    cg.add(var.set_normal_config(normal_config))

    yield automation.build_automation(var.get_idle_trigger(), [], config[CONF_IDLE_ACTION])

    if CONF_COOL_ACTION in config:
        yield automation.build_automation(var.get_cool_trigger(), [], config[CONF_COOL_ACTION])
        cg.add(var.set_supports_cool(True))
    if CONF_HEAT_ACTION in config:
        yield automation.build_automation(var.get_heat_trigger(), [], config[CONF_HEAT_ACTION])
        cg.add(var.set_supports_heat(True))

    if CONF_AWAY_CONFIG in config:
        away = config[CONF_AWAY_CONFIG]
        away_config = BangBangClimateTargetTempConfig(
            away.get(CONF_DEFAULT_TARGET_TEMPERATURE_LOW, cg.NAN),
            away.get(CONF_DEFAULT_TARGET_TEMPERATURE_HIGH, cg.NAN)
        )
        cg.add(var.set_away_config(away_config))

    if CONF_HYSTERESIS in config:
        cg.add(var.set_hysteresis(config[CONF_HYSTERESIS]))
