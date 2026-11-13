-- Students and their enrollments
CREATE TABLE students (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    enrolled_at DATE
);

CREATE TABLE enrollments (
    student_id INTEGER REFERENCES students(id),
    course TEXT NOT NULL
);

-- Number of courses per student
SELECT s.name, COUNT(e.course) AS nb_courses
FROM students s
LEFT JOIN enrollments e ON e.student_id = s.id
GROUP BY s.name;
