-- Layout all column names in database

SELECT name, 'medicare_part_d_2023' AS table_name
FROM pragma_table_info('medicare_part_d_2023')
UNION ALL
SELECT name, 'faers_demo_2023' AS table_name
FROM pragma_table_info('faers_demo_2023q1');
