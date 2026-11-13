# SQL Joins

Joins combine rows from two or more tables based on a related column.

## INNER JOIN

An INNER JOIN returns only the rows that have matching values in both tables.
It is the most common type of join.

## LEFT JOIN

A LEFT JOIN returns all rows from the left table, and the matching rows from the right table.
When there is no match, the right side columns are NULL.

# Aggregations

GROUP BY groups rows that share a value so that aggregate functions such as COUNT, SUM or AVG
can be applied to each group. HAVING filters groups after aggregation, while WHERE filters rows before.
