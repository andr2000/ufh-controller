CREATE TABLE "burner" (
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
CREATE TABLE `weather` (
	`datetime_unix`	INTEGER NOT NULL UNIQUE,
    `t_sinoptik_10` INTEGER,
    `t_sinoptik_feels_like_10` INTEGER,
	PRIMARY KEY(datetime_unix)
) WITHOUT ROWID;
CREATE TABLE "vrc700" (
	`datetime_unix`	INTEGER NOT NULL UNIQUE,
	`temp_flow_des_100`	INTEGER,
	`temp_room_des_100`	INTEGER,
	`temp_room_100`	INTEGER,
	`temp_day_100`	INTEGER,
	`temp_night_100`	INTEGER,
	`temp_out_100`	INTEGER,
	`rec_lvl_head`	INTEGER,
	`rec_lvl_out`	INTEGER,
	PRIMARY KEY(datetime_unix)
);
