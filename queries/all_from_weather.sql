SELECT
	datetime(datetime_unix, 'unixepoch', 'localtime') AS DateTime,
	(t_sinoptik_10/10.) as Toutside
FROM Weather;