SELECT DateTime,  Toutside, Flow FROM

(
SELECT
	DATETIME(datetime_unix, 'unixepoch', 'localtime') AS DateTime ,
	(t_sinoptik_10/10.) AS Toutside,
	NULL AS Flow
FROM Weather

UNION

SELECT
	DATETIME(datetime_unix, 'unixepoch', 'localtime') AS DateTime ,
	NULL AS Toutside,
	(temp_flow_100/100.) AS Flow
FROM Burner
)

ORDER BY DateTime;