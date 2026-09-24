SELECT
    s.station_code,
    s.station_name,
    (
        (
            pt.controller_datetime
            - make_interval(mins => s.utc_offset_minutes)
        ) AT TIME ZONE 'UTC'
        AT TIME ZONE 'Asia/Riyadh'
    )::date AS sales_date,
    SUM(pt.volume_litres) AS total_litres,
    SUM(pt.amount_sar) AS total_sar
FROM pump_transactions pt
JOIN stations s
    ON pt.pts_id = s.pts_id
GROUP BY
    s.station_code,
    s.station_name,
    (
        (
            pt.controller_datetime
            - make_interval(mins => s.utc_offset_minutes)
        ) AT TIME ZONE 'UTC'
        AT TIME ZONE 'Asia/Riyadh'
    )::date
ORDER BY
    sales_date,
    s.station_code;