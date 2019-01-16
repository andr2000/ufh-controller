CREATE TABLE `boiler` (
	`datetime_unix`	INTEGER NOT NULL UNIQUE,
	`temp_flow_target_100`	INTEGER,
	`temp_flow_100`	INTEGER,
	`temp_flow_sensor`	TEXT,
	`temp_return_100`	INTEGER,
	`temp_return_sensor`	TEXT,
	`flame_state`	TEXT,
	`power_hc_percent_100`	INTEGER,
	`water_pressure_1000`	INTEGER,
	`power_pump_100`	INTEGER,
	`status01`	TEXT,
	`status02`	TEXT,
	`set_mode_r`	TEXT,
	PRIMARY KEY(datetime_unix)
) WITHOUT ROWID;
