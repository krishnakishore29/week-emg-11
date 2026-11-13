CREATE SCHEMA titanic_project;

CREATE TABLE titanic_project.titanic_staging (
    name TEXT,
    sex VARCHAR(10),
    age DOUBLE PRECISION,
    sibsp INTEGER,
    parch INTEGER,
    embarked VARCHAR(5),
    ticket TEXT,
    fare DOUBLE PRECISION,
    cabin TEXT,
    passengerid INTEGER,
    pclass INTEGER,
    survived INTEGER
);

\copy titanic_project.titanic_staging FROM 'C:/Users/krish/OneDrive/Desktop/emg lab 11/Titanic-Dataset.csv' WITH (FORMAT CSV, HEADER TRUE)

CREATE TABLE titanic_project.passengers (
    name TEXT,
    sex VARCHAR(10),
    age DOUBLE PRECISION,
    sibsp INTEGER,
    parch INTEGER,
    embarked VARCHAR(5),
    ticket TEXT,
    fare DOUBLE PRECISION,
    cabin TEXT,
    passengerid INTEGER PRIMARY KEY,
    pclass INTEGER CHECK (pclass IN (1, 2, 3)),
    survived INTEGER CHECK (survived IN (0, 1))
);

INSERT INTO titanic_project.passengers
SELECT name, sex, age, sibsp, parch, embarked, ticket, fare, cabin,
       passengerid, pclass, survived
FROM titanic_project.titanic_staging;
