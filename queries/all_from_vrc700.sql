SELECT
	datetime(datetime_unix, 'unixepoch', 'localtime') AS DateTime ,
	(temp_flow_des_100/100.) as FlowD,
	(temp_room_des_100/100.) as RoomD,
	(temp_room_100/100.) as RoomT,
	(temp_day_100/100.) as DayT,
	(temp_night_100/100.) as NightT,
	(temp_out_100/100.) as OutT,
	rec_lvl_head as LvlHead,
	rec_lvl_out as LvlOut
FROM VRC700 WHERE DateTime BETWEEN datetime('now', 'start of day') AND datetime('now', 'localtime');
/* FROM VRC700 WHERE DateTime BETWEEN datetime('now', '-1 days') AND datetime('now', 'localtime'); */