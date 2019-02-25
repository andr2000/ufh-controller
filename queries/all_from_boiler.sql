SELECT
	datetime(datetime_unix, 'unixepoch', 'localtime') AS DateTime ,
	(temp_flow_target_100/100.) as FlowTarget,
	(temp_flow_100/100.) as Flow,
	temp_flow_sensor as FlowSensor,
	(temp_return_100/100.) as Return,
	temp_return_sensor as ReturnSensor,
	(flame_state = 'on' ) as Flame,
	(power_hc_percent_100/100.) as PowPercent,
	(power_hc_percent_100/100 * 20./100.) as PowerKW,
	(water_pressure_1000/1000.) as WaterPressure,
	(power_pump_100/100.) as PumpPower,
	status01 as S01, status02 as S02, set_mode_r as SetMode
FROM Boiler WHERE DateTime BETWEEN datetime('now', 'start of day') AND datetime('now', 'localtime');
/* FROM Boiler WHERE DateTime BETWEEN datetime('now', '-1 days') AND datetime('now', 'localtime'); */