SELECT
	datetime(datetime_unix, 'unixepoch', 'localtime') AS DateTime,
	(t_sinoptik_10/10.) as Toutside,
	(t_sinoptik_feels_like_10/10.) as Tfeels
FROM Weather WHERE DateTime BETWEEN datetime('now', 'start of day') AND datetime('now', 'localtime');
/* FROM Weather WHERE DateTime BETWEEN datetime('now', '-1 days') AND datetime('now', 'localtime'); */