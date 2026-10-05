from homeassistant.const import EntityCategory
from bluetti_bt_connect_lib import FieldName


DIAGNOSTICS = [
    FieldName.DEVICE_SN,
    FieldName.DEVICE_TYPE,
    FieldName.VER_ARM,
    FieldName.VER_DSP,
    FieldName.VER_BMS,
    FieldName.PACK_CELL_VOLTAGES,
    FieldName.CONNECTED_DEVICES,
    FieldName.TEMPERATURE_SENSOR_COUNT,
    FieldName.FIRMWARE_ARM,
    FieldName.FIRMWARE_DSP,
    FieldName.FIRMWARE_IOT,
    FieldName.WIFI_SIGNAL,
    FieldName.CLOUD_CONNECTED,
    FieldName.EMS_CONTROL_MODE,
    FieldName.ALARM_COUNT,
    FieldName.SYSTEM_ERROR,
    FieldName.MAX_CHARGE_CURRENT,
    FieldName.MAX_DISCHARGE_CURRENT,
    FieldName.TIME_CONTROL_ENABLED,
    FieldName.SCHEDULE_SLOT_1,
    FieldName.SCHEDULE_SLOT_2,
    FieldName.SCHEDULE_SLOT_3,
    FieldName.SCHEDULE_SLOT_4,
    FieldName.SCHEDULE_SLOT_5,
    FieldName.SCHEDULE_SLOT_6,
    FieldName.AC_PV_L1_VOLTAGE,
    FieldName.AC_PV_L2_VOLTAGE,
    FieldName.AC_PV_L3_VOLTAGE,
]

CONFIGS = [
    FieldName.CTRL_CHARGING_MODE,
    FieldName.CTRL_DISPLAY_TIMEOUT,
    FieldName.CTRL_ECO,
    FieldName.CTRL_ECO_AC,
    FieldName.CTRL_ECO_DC,
    FieldName.CTRL_ECO_MIN_POWER_AC,
    FieldName.CTRL_ECO_MIN_POWER_DC,
    FieldName.CTRL_ECO_TIME_MODE,
    FieldName.CTRL_ECO_TIME_MODE_AC,
    FieldName.CTRL_ECO_TIME_MODE_DC,
    FieldName.CTRL_POWER_LIFTING,
    FieldName.CTRL_SPLIT_PHASE,
    FieldName.CTRL_UPS_MODE,
]


def get_category(field: FieldName) -> EntityCategory | None:
    if field in DIAGNOSTICS:
        return EntityCategory.DIAGNOSTIC
    if field in CONFIGS:
        return EntityCategory.CONFIG
    return None
