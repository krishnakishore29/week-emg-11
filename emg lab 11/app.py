"""Titanic Passenger Explorer: a PostgreSQL, Python, and Streamlit lab app.

This app reads the imported Titanic CSV from the staging table. It includes
an interactive dashboard, a passenger search tool, an SQL lesson library,
a quiz, and a small data dictionary. It uses plain Python row dictionaries
instead of pandas because Windows blocked a compiled pandas extension.
"""

import csv
import html
import io
import os
from collections import Counter

import psycopg2
from psycopg2.extras import RealDictCursor
import streamlit as st

TABLE = "titanic_project.titanic_staging"

st.set_page_config(
    page_title="Titanic Passenger Explorer",
    page_icon="🚢",
    layout="wide",
    initial_sidebar_state="expanded",
)

with st.sidebar:
    st.header("Database connection")
    st.caption("Enter the same password you use for PostgreSQL.")
    db_password = st.text_input("PostgreSQL password", type="password")
    st.caption("Database: titanic_db")
    st.caption("Data: titanic_project.titanic_staging")


def connect():
    """Connect to the local PostgreSQL server."""
    return psycopg2.connect(
        host=os.getenv("PGHOST", "localhost"),
        port=os.getenv("PGPORT", "5432"),
        dbname=os.getenv("PGDATABASE", "titanic_db"),
        user=os.getenv("PGUSER", "postgres"),
        password=db_password or os.getenv("PGPASSWORD", ""),
        connect_timeout=5,
    )


def run_query(sql, params=None):
    """Execute a query and return a list of plain Python dictionaries."""
    with connect() as connection:
        with connection.cursor(cursor_factory=RealDictCursor) as cursor:
            cursor.execute(sql, params or ())
            if cursor.description is None:
                return []
            return [dict(record) for record in cursor.fetchall()]


def safe_cell(value):
    """Escape a cell for a Markdown table."""
    if value is None:
        return ""
    if isinstance(value, float):
        value = f"{value:.2f}"
    return html.escape(str(value)).replace("|", "&#124;").replace("\n", " ")


def display_table(records, limit=100):
    """Render result dictionaries without importing pandas."""
    if not records:
        st.info("No rows match this choice.")
        return
    fields = list(records[0].keys())
    lines = [
        "| " + " | ".join(safe_cell(field) for field in fields) + " |",
        "| " + " | ".join("---" for field in fields) + " |",
    ]
    for record in records[:limit]:
        lines.append("| " + " | ".join(safe_cell(record.get(field)) for field in fields) + " |")
    st.markdown("\n".join(lines))
    if len(records) > limit:
        st.caption(f"Showing {limit} rows from a result of {len(records):,}.")


def create_csv(records):
    """Make browser-downloadable CSV text."""
    if not records:
        return ""
    output = io.StringIO()
    writer = csv.DictWriter(output, fieldnames=list(records[0].keys()))
    writer.writeheader()
    writer.writerows(records)
    return output.getvalue()


def value_counts(records, field):
    """Count values in a field and label missing values clearly."""
    counts = Counter()
    for record in records:
        value = record.get(field)
        counts["(missing)" if value is None else str(value)] += 1
    return counts


def draw_bar(label, value, maximum):
    """Draw a tiny text bar using only Streamlit text."""
    width = 0 if maximum <= 0 else min(32, round(value * 32 / maximum))
    st.write(f"**{label}**  <code>{'█' * width}</code>  {value:,}", unsafe_allow_html=True)


def describe_columns():
    """Explain the original Titanic CSV fields."""
    return [
        {"column": "name", "meaning": "Passenger name and title"},
        {"column": "sex", "meaning": "Recorded sex label"},
        {"column": "age", "meaning": "Passenger age; some values are missing"},
        {"column": "sibsp", "meaning": "Siblings and spouses aboard"},
        {"column": "parch", "meaning": "Parents and children aboard"},
        {"column": "embarked", "meaning": "Boarding port code"},
        {"column": "ticket", "meaning": "Ticket identifier"},
        {"column": "fare", "meaning": "Ticket fare"},
        {"column": "cabin", "meaning": "Cabin identifier; many are missing"},
        {"column": "passengerid", "meaning": "Passenger number in the source file"},
        {"column": "pclass", "meaning": "Passenger class: 1, 2, or 3"},
        {"column": "survived", "meaning": "1 means yes; 0 means no"},
    ]


COLUMN_GUIDE = describe_columns()

try:
    passengers = run_query(f"SELECT * FROM {TABLE} ORDER BY passengerid")
except Exception as database_error:
    st.title("Titanic Passenger Explorer")
    st.error("I could not read the imported Titanic data.")
    st.caption("Check PostgreSQL, the password box, and the staging table.")
    st.code(str(database_error))
    st.stop()

if not passengers:
    st.title("Titanic Passenger Explorer")
    st.warning("The staging table is empty. Import the Titanic CSV first.")
    st.stop()

total_passengers = len(passengers)
survivors = sum(int(row.get("survived") or 0) for row in passengers)
survival_percent = 100 * survivors / total_passengers if total_passengers else 0

st.title("🚢 Titanic Passenger Explorer")
st.write("Explore passenger records and practise SQL with prepared examples.")


SQL_LESSONS = [
    {
        'title': 'Count all passengers',
        'topic': 'COUNT',
        'description': 'COUNT(*) counts all rows, including rows with blanks.',
        'sql': 'SELECT COUNT(*) AS passengers FROM titanic_project.titanic_staging;',
    },
    {
        'title': 'Preview ten passengers',
        'topic': 'LIMIT',
        'description': 'LIMIT keeps a preview short.',
        'sql': 'SELECT passengerid, name, sex, age FROM titanic_project.titanic_staging ORDER BY passengerid LIMIT 10;',
    },
    {
        'title': 'Count survival results',
        'topic': 'GROUP BY',
        'description': 'The survived field uses one for yes and zero for no.',
        'sql': 'SELECT survived, COUNT(*) AS passengers FROM titanic_project.titanic_staging GROUP BY survived ORDER BY survived;',
    },
    {
        'title': 'Count known ages',
        'topic': 'COUNT(column)',
        'description': 'COUNT(age) skips missing age values.',
        'sql': 'SELECT COUNT(age) AS known_ages FROM titanic_project.titanic_staging;',
    },
    {
        'title': 'Find missing ages',
        'topic': 'IS NULL',
        'description': 'IS NULL finds records without a known age.',
        'sql': 'SELECT passengerid, name FROM titanic_project.titanic_staging WHERE age IS NULL ORDER BY passengerid LIMIT 30;',
    },
    {
        'title': 'Find recorded cabins',
        'topic': 'IS NOT NULL',
        'description': 'IS NOT NULL finds rows with a cabin value.',
        'sql': 'SELECT passengerid, name, cabin FROM titanic_project.titanic_staging WHERE cabin IS NOT NULL ORDER BY passengerid LIMIT 30;',
    },
    {
        'title': 'Calculate average age',
        'topic': 'AVG',
        'description': 'AVG skips NULL values.',
        'sql': 'SELECT ROUND(AVG(age)::numeric, 1) AS average_age FROM titanic_project.titanic_staging;',
    },
    {
        'title': 'Find the smallest and largest fares',
        'topic': 'MIN and MAX',
        'description': 'MIN and MAX show numeric extremes.',
        'sql': 'SELECT MIN(fare) AS smallest_fare, MAX(fare) AS largest_fare FROM titanic_project.titanic_staging;',
    },
    {
        'title': 'Count passengers by sex',
        'topic': 'GROUP BY',
        'description': 'Make one group for each sex label.',
        'sql': 'SELECT sex, COUNT(*) AS passengers FROM titanic_project.titanic_staging GROUP BY sex ORDER BY sex;',
    },
    {
        'title': 'Count passengers by class',
        'topic': 'GROUP BY',
        'description': 'Passenger classes are one, two, and three.',
        'sql': 'SELECT pclass, COUNT(*) AS passengers FROM titanic_project.titanic_staging GROUP BY pclass ORDER BY pclass;',
    },
    {
        'title': 'Count passengers by port',
        'topic': 'GROUP BY',
        'description': 'Embarked stores the boarding port code.',
        'sql': 'SELECT embarked, COUNT(*) AS passengers FROM titanic_project.titanic_staging GROUP BY embarked ORDER BY embarked;',
    },
    {
        'title': 'Calculate survival percentage',
        'topic': 'AVG',
        'description': 'The average of a zero-or-one field is its percentage as a fraction.',
        'sql': 'SELECT ROUND(AVG(survived)::numeric * 100, 1) AS survival_percent FROM titanic_project.titanic_staging;',
    },
    {
        'title': 'Average fare by class',
        'topic': 'AVG and GROUP BY',
        'description': 'Compare ticket fares for the different classes.',
        'sql': 'SELECT pclass, ROUND(AVG(fare)::numeric, 2) AS average_fare FROM titanic_project.titanic_staging GROUP BY pclass ORDER BY pclass;',
    },
    {
        'title': 'Average age by class',
        'topic': 'AVG and GROUP BY',
        'description': 'Missing ages are ignored by AVG.',
        'sql': 'SELECT pclass, ROUND(AVG(age)::numeric, 1) AS average_age FROM titanic_project.titanic_staging GROUP BY pclass ORDER BY pclass;',
    },
    {
        'title': 'Fares above the overall average',
        'topic': 'Subquery',
        'description': 'The subquery calculates the average first.',
        'sql': 'SELECT passengerid, name, fare FROM titanic_project.titanic_staging WHERE fare > (SELECT AVG(fare) FROM titanic_project.titanic_staging) ORDER BY fare DESC LIMIT 30;',
    },
    {
        'title': 'Count by child or adult age group',
        'topic': 'CASE',
        'description': 'CASE creates a label from a rule.',
        'sql': "SELECT CASE WHEN age < 18 THEN 'Child' WHEN age >= 18 THEN 'Adult' ELSE 'Age missing' END AS age_group, COUNT(*) AS passengers FROM titanic_project.titanic_staging GROUP BY age_group ORDER BY age_group;",
    },
    {
        'title': 'Count missing cabins',
        'topic': 'COUNT and NULL',
        'description': 'Subtract recorded cabins from all rows to find missing cabins.',
        'sql': 'SELECT COUNT(*) - COUNT(cabin) AS missing_cabins FROM titanic_project.titanic_staging;',
    },
    {
        'title': 'Count passengers by sex (extra example)',
        'topic': 'Grouping and aggregates',
        'description': 'Group the records by sex, then calculate count passengers.',
        'sql': 'SELECT sex, ROUND((COUNT(*))::numeric, 2) AS passenger_count FROM titanic_project.titanic_staging GROUP BY sex ORDER BY sex;',
    },
    {
        'title': 'Average age by sex',
        'topic': 'Grouping and aggregates',
        'description': 'Group the records by sex, then calculate average age.',
        'sql': 'SELECT sex, ROUND((AVG(age))::numeric, 2) AS average_age FROM titanic_project.titanic_staging GROUP BY sex ORDER BY sex;',
    },
    {
        'title': 'Average fare by sex',
        'topic': 'Grouping and aggregates',
        'description': 'Group the records by sex, then calculate average fare.',
        'sql': 'SELECT sex, ROUND((AVG(fare))::numeric, 2) AS average_fare FROM titanic_project.titanic_staging GROUP BY sex ORDER BY sex;',
    },
    {
        'title': 'Survival percentage by sex',
        'topic': 'Grouping and aggregates',
        'description': 'Group the records by sex, then calculate survival percentage.',
        'sql': 'SELECT sex, ROUND((AVG(survived) * 100)::numeric, 2) AS survival_percent FROM titanic_project.titanic_staging GROUP BY sex ORDER BY sex;',
    },
    {
        'title': 'Count passengers by passenger class',
        'topic': 'Grouping and aggregates',
        'description': 'Group the records by passenger class, then calculate count passengers.',
        'sql': 'SELECT pclass, ROUND((COUNT(*))::numeric, 2) AS passenger_count FROM titanic_project.titanic_staging GROUP BY pclass ORDER BY pclass;',
    },
    {
        'title': 'Average age by passenger class',
        'topic': 'Grouping and aggregates',
        'description': 'Group the records by passenger class, then calculate average age.',
        'sql': 'SELECT pclass, ROUND((AVG(age))::numeric, 2) AS average_age FROM titanic_project.titanic_staging GROUP BY pclass ORDER BY pclass;',
    },
    {
        'title': 'Average fare by passenger class',
        'topic': 'Grouping and aggregates',
        'description': 'Group the records by passenger class, then calculate average fare.',
        'sql': 'SELECT pclass, ROUND((AVG(fare))::numeric, 2) AS average_fare FROM titanic_project.titanic_staging GROUP BY pclass ORDER BY pclass;',
    },
    {
        'title': 'Survival percentage by passenger class',
        'topic': 'Grouping and aggregates',
        'description': 'Group the records by passenger class, then calculate survival percentage.',
        'sql': 'SELECT pclass, ROUND((AVG(survived) * 100)::numeric, 2) AS survival_percent FROM titanic_project.titanic_staging GROUP BY pclass ORDER BY pclass;',
    },
    {
        'title': 'Count passengers by boarding port',
        'topic': 'Grouping and aggregates',
        'description': 'Group the records by boarding port, then calculate count passengers.',
        'sql': 'SELECT embarked, ROUND((COUNT(*))::numeric, 2) AS passenger_count FROM titanic_project.titanic_staging GROUP BY embarked ORDER BY embarked;',
    },
    {
        'title': 'Average age by boarding port',
        'topic': 'Grouping and aggregates',
        'description': 'Group the records by boarding port, then calculate average age.',
        'sql': 'SELECT embarked, ROUND((AVG(age))::numeric, 2) AS average_age FROM titanic_project.titanic_staging GROUP BY embarked ORDER BY embarked;',
    },
    {
        'title': 'Average fare by boarding port',
        'topic': 'Grouping and aggregates',
        'description': 'Group the records by boarding port, then calculate average fare.',
        'sql': 'SELECT embarked, ROUND((AVG(fare))::numeric, 2) AS average_fare FROM titanic_project.titanic_staging GROUP BY embarked ORDER BY embarked;',
    },
    {
        'title': 'Survival percentage by boarding port',
        'topic': 'Grouping and aggregates',
        'description': 'Group the records by boarding port, then calculate survival percentage.',
        'sql': 'SELECT embarked, ROUND((AVG(survived) * 100)::numeric, 2) AS survival_percent FROM titanic_project.titanic_staging GROUP BY embarked ORDER BY embarked;',
    },
    {
        'title': 'Count passengers by survival result',
        'topic': 'Grouping and aggregates',
        'description': 'Group the records by survival result, then calculate count passengers.',
        'sql': 'SELECT survived, ROUND((COUNT(*))::numeric, 2) AS passenger_count FROM titanic_project.titanic_staging GROUP BY survived ORDER BY survived;',
    },
    {
        'title': 'Average age by survival result',
        'topic': 'Grouping and aggregates',
        'description': 'Group the records by survival result, then calculate average age.',
        'sql': 'SELECT survived, ROUND((AVG(age))::numeric, 2) AS average_age FROM titanic_project.titanic_staging GROUP BY survived ORDER BY survived;',
    },
    {
        'title': 'Average fare by survival result',
        'topic': 'Grouping and aggregates',
        'description': 'Group the records by survival result, then calculate average fare.',
        'sql': 'SELECT survived, ROUND((AVG(fare))::numeric, 2) AS average_fare FROM titanic_project.titanic_staging GROUP BY survived ORDER BY survived;',
    },
    {
        'title': 'Survival percentage by survival result',
        'topic': 'Grouping and aggregates',
        'description': 'Group the records by survival result, then calculate survival percentage.',
        'sql': 'SELECT survived, ROUND((AVG(survived) * 100)::numeric, 2) AS survival_percent FROM titanic_project.titanic_staging GROUP BY survived ORDER BY survived;',
    },
    {
        'title': 'Count passengers by siblings or spouses',
        'topic': 'Grouping and aggregates',
        'description': 'Group the records by siblings or spouses, then calculate count passengers.',
        'sql': 'SELECT sibsp, ROUND((COUNT(*))::numeric, 2) AS passenger_count FROM titanic_project.titanic_staging GROUP BY sibsp ORDER BY sibsp;',
    },
    {
        'title': 'Average age by siblings or spouses',
        'topic': 'Grouping and aggregates',
        'description': 'Group the records by siblings or spouses, then calculate average age.',
        'sql': 'SELECT sibsp, ROUND((AVG(age))::numeric, 2) AS average_age FROM titanic_project.titanic_staging GROUP BY sibsp ORDER BY sibsp;',
    },
    {
        'title': 'Average fare by siblings or spouses',
        'topic': 'Grouping and aggregates',
        'description': 'Group the records by siblings or spouses, then calculate average fare.',
        'sql': 'SELECT sibsp, ROUND((AVG(fare))::numeric, 2) AS average_fare FROM titanic_project.titanic_staging GROUP BY sibsp ORDER BY sibsp;',
    },
    {
        'title': 'Survival percentage by siblings or spouses',
        'topic': 'Grouping and aggregates',
        'description': 'Group the records by siblings or spouses, then calculate survival percentage.',
        'sql': 'SELECT sibsp, ROUND((AVG(survived) * 100)::numeric, 2) AS survival_percent FROM titanic_project.titanic_staging GROUP BY sibsp ORDER BY sibsp;',
    },
    {
        'title': 'Count passengers by parents or children',
        'topic': 'Grouping and aggregates',
        'description': 'Group the records by parents or children, then calculate count passengers.',
        'sql': 'SELECT parch, ROUND((COUNT(*))::numeric, 2) AS passenger_count FROM titanic_project.titanic_staging GROUP BY parch ORDER BY parch;',
    },
    {
        'title': 'Average age by parents or children',
        'topic': 'Grouping and aggregates',
        'description': 'Group the records by parents or children, then calculate average age.',
        'sql': 'SELECT parch, ROUND((AVG(age))::numeric, 2) AS average_age FROM titanic_project.titanic_staging GROUP BY parch ORDER BY parch;',
    },
    {
        'title': 'Average fare by parents or children',
        'topic': 'Grouping and aggregates',
        'description': 'Group the records by parents or children, then calculate average fare.',
        'sql': 'SELECT parch, ROUND((AVG(fare))::numeric, 2) AS average_fare FROM titanic_project.titanic_staging GROUP BY parch ORDER BY parch;',
    },
    {
        'title': 'Survival percentage by parents or children',
        'topic': 'Grouping and aggregates',
        'description': 'Group the records by parents or children, then calculate survival percentage.',
        'sql': 'SELECT parch, ROUND((AVG(survived) * 100)::numeric, 2) AS survival_percent FROM titanic_project.titanic_staging GROUP BY parch ORDER BY parch;',
    },
    {
        'title': 'Count by sex and pclass',
        'topic': 'Two-column grouping',
        'description': 'Make one group for each combination of sex and pclass.',
        'sql': 'SELECT sex, pclass, COUNT(*) AS passengers FROM titanic_project.titanic_staging GROUP BY sex, pclass ORDER BY sex, pclass;',
    },
    {
        'title': 'Average fare by sex and pclass',
        'topic': 'Two-column grouping',
        'description': 'Compare average ticket prices in smaller groups.',
        'sql': 'SELECT sex, pclass, ROUND(AVG(fare)::numeric, 2) AS average_fare FROM titanic_project.titanic_staging GROUP BY sex, pclass ORDER BY sex, pclass;',
    },
    {
        'title': 'Count by sex and embarked',
        'topic': 'Two-column grouping',
        'description': 'Make one group for each combination of sex and embarked.',
        'sql': 'SELECT sex, embarked, COUNT(*) AS passengers FROM titanic_project.titanic_staging GROUP BY sex, embarked ORDER BY sex, embarked;',
    },
    {
        'title': 'Average fare by sex and embarked',
        'topic': 'Two-column grouping',
        'description': 'Compare average ticket prices in smaller groups.',
        'sql': 'SELECT sex, embarked, ROUND(AVG(fare)::numeric, 2) AS average_fare FROM titanic_project.titanic_staging GROUP BY sex, embarked ORDER BY sex, embarked;',
    },
    {
        'title': 'Count by sex and survived',
        'topic': 'Two-column grouping',
        'description': 'Make one group for each combination of sex and survived.',
        'sql': 'SELECT sex, survived, COUNT(*) AS passengers FROM titanic_project.titanic_staging GROUP BY sex, survived ORDER BY sex, survived;',
    },
    {
        'title': 'Average fare by sex and survived',
        'topic': 'Two-column grouping',
        'description': 'Compare average ticket prices in smaller groups.',
        'sql': 'SELECT sex, survived, ROUND(AVG(fare)::numeric, 2) AS average_fare FROM titanic_project.titanic_staging GROUP BY sex, survived ORDER BY sex, survived;',
    },
    {
        'title': 'Count by sex and sibsp',
        'topic': 'Two-column grouping',
        'description': 'Make one group for each combination of sex and sibsp.',
        'sql': 'SELECT sex, sibsp, COUNT(*) AS passengers FROM titanic_project.titanic_staging GROUP BY sex, sibsp ORDER BY sex, sibsp;',
    },
    {
        'title': 'Average fare by sex and sibsp',
        'topic': 'Two-column grouping',
        'description': 'Compare average ticket prices in smaller groups.',
        'sql': 'SELECT sex, sibsp, ROUND(AVG(fare)::numeric, 2) AS average_fare FROM titanic_project.titanic_staging GROUP BY sex, sibsp ORDER BY sex, sibsp;',
    },
    {
        'title': 'Count by sex and parch',
        'topic': 'Two-column grouping',
        'description': 'Make one group for each combination of sex and parch.',
        'sql': 'SELECT sex, parch, COUNT(*) AS passengers FROM titanic_project.titanic_staging GROUP BY sex, parch ORDER BY sex, parch;',
    },
    {
        'title': 'Average fare by sex and parch',
        'topic': 'Two-column grouping',
        'description': 'Compare average ticket prices in smaller groups.',
        'sql': 'SELECT sex, parch, ROUND(AVG(fare)::numeric, 2) AS average_fare FROM titanic_project.titanic_staging GROUP BY sex, parch ORDER BY sex, parch;',
    },
    {
        'title': 'Count by pclass and embarked',
        'topic': 'Two-column grouping',
        'description': 'Make one group for each combination of pclass and embarked.',
        'sql': 'SELECT pclass, embarked, COUNT(*) AS passengers FROM titanic_project.titanic_staging GROUP BY pclass, embarked ORDER BY pclass, embarked;',
    },
    {
        'title': 'Average fare by pclass and embarked',
        'topic': 'Two-column grouping',
        'description': 'Compare average ticket prices in smaller groups.',
        'sql': 'SELECT pclass, embarked, ROUND(AVG(fare)::numeric, 2) AS average_fare FROM titanic_project.titanic_staging GROUP BY pclass, embarked ORDER BY pclass, embarked;',
    },
    {
        'title': 'Count by pclass and survived',
        'topic': 'Two-column grouping',
        'description': 'Make one group for each combination of pclass and survived.',
        'sql': 'SELECT pclass, survived, COUNT(*) AS passengers FROM titanic_project.titanic_staging GROUP BY pclass, survived ORDER BY pclass, survived;',
    },
    {
        'title': 'Average fare by pclass and survived',
        'topic': 'Two-column grouping',
        'description': 'Compare average ticket prices in smaller groups.',
        'sql': 'SELECT pclass, survived, ROUND(AVG(fare)::numeric, 2) AS average_fare FROM titanic_project.titanic_staging GROUP BY pclass, survived ORDER BY pclass, survived;',
    },
    {
        'title': 'Count by pclass and sibsp',
        'topic': 'Two-column grouping',
        'description': 'Make one group for each combination of pclass and sibsp.',
        'sql': 'SELECT pclass, sibsp, COUNT(*) AS passengers FROM titanic_project.titanic_staging GROUP BY pclass, sibsp ORDER BY pclass, sibsp;',
    },
    {
        'title': 'Average fare by pclass and sibsp',
        'topic': 'Two-column grouping',
        'description': 'Compare average ticket prices in smaller groups.',
        'sql': 'SELECT pclass, sibsp, ROUND(AVG(fare)::numeric, 2) AS average_fare FROM titanic_project.titanic_staging GROUP BY pclass, sibsp ORDER BY pclass, sibsp;',
    },
    {
        'title': 'Count by pclass and parch',
        'topic': 'Two-column grouping',
        'description': 'Make one group for each combination of pclass and parch.',
        'sql': 'SELECT pclass, parch, COUNT(*) AS passengers FROM titanic_project.titanic_staging GROUP BY pclass, parch ORDER BY pclass, parch;',
    },
    {
        'title': 'Average fare by pclass and parch',
        'topic': 'Two-column grouping',
        'description': 'Compare average ticket prices in smaller groups.',
        'sql': 'SELECT pclass, parch, ROUND(AVG(fare)::numeric, 2) AS average_fare FROM titanic_project.titanic_staging GROUP BY pclass, parch ORDER BY pclass, parch;',
    },
    {
        'title': 'Count by embarked and survived',
        'topic': 'Two-column grouping',
        'description': 'Make one group for each combination of embarked and survived.',
        'sql': 'SELECT embarked, survived, COUNT(*) AS passengers FROM titanic_project.titanic_staging GROUP BY embarked, survived ORDER BY embarked, survived;',
    },
    {
        'title': 'Average fare by embarked and survived',
        'topic': 'Two-column grouping',
        'description': 'Compare average ticket prices in smaller groups.',
        'sql': 'SELECT embarked, survived, ROUND(AVG(fare)::numeric, 2) AS average_fare FROM titanic_project.titanic_staging GROUP BY embarked, survived ORDER BY embarked, survived;',
    },
    {
        'title': 'Count by embarked and sibsp',
        'topic': 'Two-column grouping',
        'description': 'Make one group for each combination of embarked and sibsp.',
        'sql': 'SELECT embarked, sibsp, COUNT(*) AS passengers FROM titanic_project.titanic_staging GROUP BY embarked, sibsp ORDER BY embarked, sibsp;',
    },
    {
        'title': 'Average fare by embarked and sibsp',
        'topic': 'Two-column grouping',
        'description': 'Compare average ticket prices in smaller groups.',
        'sql': 'SELECT embarked, sibsp, ROUND(AVG(fare)::numeric, 2) AS average_fare FROM titanic_project.titanic_staging GROUP BY embarked, sibsp ORDER BY embarked, sibsp;',
    },
    {
        'title': 'Count by embarked and parch',
        'topic': 'Two-column grouping',
        'description': 'Make one group for each combination of embarked and parch.',
        'sql': 'SELECT embarked, parch, COUNT(*) AS passengers FROM titanic_project.titanic_staging GROUP BY embarked, parch ORDER BY embarked, parch;',
    },
    {
        'title': 'Average fare by embarked and parch',
        'topic': 'Two-column grouping',
        'description': 'Compare average ticket prices in smaller groups.',
        'sql': 'SELECT embarked, parch, ROUND(AVG(fare)::numeric, 2) AS average_fare FROM titanic_project.titanic_staging GROUP BY embarked, parch ORDER BY embarked, parch;',
    },
    {
        'title': 'Count by survived and sibsp',
        'topic': 'Two-column grouping',
        'description': 'Make one group for each combination of survived and sibsp.',
        'sql': 'SELECT survived, sibsp, COUNT(*) AS passengers FROM titanic_project.titanic_staging GROUP BY survived, sibsp ORDER BY survived, sibsp;',
    },
    {
        'title': 'Average fare by survived and sibsp',
        'topic': 'Two-column grouping',
        'description': 'Compare average ticket prices in smaller groups.',
        'sql': 'SELECT survived, sibsp, ROUND(AVG(fare)::numeric, 2) AS average_fare FROM titanic_project.titanic_staging GROUP BY survived, sibsp ORDER BY survived, sibsp;',
    },
    {
        'title': 'Count by survived and parch',
        'topic': 'Two-column grouping',
        'description': 'Make one group for each combination of survived and parch.',
        'sql': 'SELECT survived, parch, COUNT(*) AS passengers FROM titanic_project.titanic_staging GROUP BY survived, parch ORDER BY survived, parch;',
    },
]
QUIZ_QUESTIONS = [
    {
        'question': 'What does COUNT(*) count?',
        'options': ['Every row', 'Only complete rows', 'Only the first column'],
        'answer': 'Every row',
        'explanation': 'COUNT(*) counts every row.',
    },
    {
        'question': 'What does COUNT(age) skip?',
        'options': ['Rows where age is NULL', 'Rows where age is zero', 'Rows older than 18'],
        'answer': 'Rows where age is NULL',
        'explanation': 'COUNT(column) skips NULL values.',
    },
    {
        'question': 'Which clause filters individual rows?',
        'options': ['WHERE', 'HAVING', 'ORDER BY'],
        'answer': 'WHERE',
        'explanation': 'WHERE filters records before groups are made.',
    },
    {
        'question': 'Which clause filters groups?',
        'options': ['HAVING', 'LIMIT', 'FROM'],
        'answer': 'HAVING',
        'explanation': 'HAVING filters groups after GROUP BY.',
    },
    {
        'question': 'What does GROUP BY do?',
        'options': ['Groups matching values', 'Deletes rows', 'Renames columns'],
        'answer': 'Groups matching values',
        'explanation': 'GROUP BY makes groups for summaries.',
    },
    {
        'question': 'What does ORDER BY do?',
        'options': ['Sorts results', 'Counts rows', 'Creates tables'],
        'answer': 'Sorts results',
        'explanation': 'ORDER BY changes the result order.',
    },
    {
        'question': 'What does LIMIT 10 do?',
        'options': ['Returns at most ten rows', 'Deletes ten rows', 'Skips ten columns'],
        'answer': 'Returns at most ten rows',
        'explanation': 'LIMIT sets the maximum result size.',
    },
    {
        'question': 'What does NULL mean?',
        'options': ['Missing or unknown', 'The number zero', 'An empty database'],
        'answer': 'Missing or unknown',
        'explanation': 'NULL is not the same as zero.',
    },
    {
        'question': 'How do you find a missing age?',
        'options': ['age IS NULL', 'age = NULL', 'age == blank'],
        'answer': 'age IS NULL',
        'explanation': 'SQL uses IS NULL to find missing values.',
    },
    {
        'question': 'What does AVG(fare) calculate?',
        'options': ['Average fare', 'Largest fare', 'Number of fares'],
        'answer': 'Average fare',
        'explanation': 'AVG calculates the arithmetic mean.',
    },
    {
        'question': 'What does MIN(fare) return?',
        'options': ['Smallest fare', 'Average fare', 'Most common fare'],
        'answer': 'Smallest fare',
        'explanation': 'MIN returns the smallest known value.',
    },
    {
        'question': 'What does MAX(fare) return?',
        'options': ['Largest fare', 'Average fare', 'Passenger count'],
        'answer': 'Largest fare',
        'explanation': 'MAX returns the largest known value.',
    },
    {
        'question': 'What does survived = 1 mean?',
        'options': ['Passenger survived', 'Passenger was class 1', 'Fare was one'],
        'answer': 'Passenger survived',
        'explanation': 'The source uses one for yes.',
    },
    {
        'question': 'What does survived = 0 mean?',
        'options': ['Passenger did not survive', 'Passenger was class zero', 'Age is missing'],
        'answer': 'Passenger did not survive',
        'explanation': 'The source uses zero for no.',
    },
    {
        'question': 'Which keyword returns unique values?',
        'options': ['DISTINCT', 'UNIQUE BY', 'ONLY'],
        'answer': 'DISTINCT',
        'explanation': 'SELECT DISTINCT removes repeated values.',
    },
    {
        'question': 'What does ILIKE do?',
        'options': ['Case-insensitive text search', 'Turns text into a number', 'Counts missing rows'],
        'answer': 'Case-insensitive text search',
        'explanation': 'PostgreSQL ILIKE ignores letter case.',
    },
    {
        'question': 'What does AND require?',
        'options': ['Both conditions match', 'Either condition matches', 'No condition matches'],
        'answer': 'Both conditions match',
        'explanation': 'AND keeps rows only when both checks pass.',
    },
    {
        'question': 'What does OR require?',
        'options': ['At least one condition matches', 'Both conditions are false', 'A missing value'],
        'answer': 'At least one condition matches',
        'explanation': 'OR keeps rows when one or both checks pass.',
    },
    {
        'question': 'How many rows are in this dataset?',
        'options': ['891', '714', '204'],
        'answer': '891',
        'explanation': 'The CSV has 891 passenger rows.',
    },
    {
        'question': 'How many columns are in the source CSV?',
        'options': ['12', '3', '891'],
        'answer': '12',
        'explanation': 'The source CSV has twelve columns.',
    },
    {
        'question': 'Which field stores names?',
        'options': ['name', 'fare', 'pclass'],
        'answer': 'name',
        'explanation': 'The name column stores passenger names.',
    },
    {
        'question': 'Which field stores ticket price?',
        'options': ['fare', 'cabin', 'ticket'],
        'answer': 'fare',
        'explanation': 'Fare stores ticket cost.',
    },
    {
        'question': 'Which field stores passenger class?',
        'options': ['pclass', 'parch', 'embarked'],
        'answer': 'pclass',
        'explanation': 'pclass is one, two, or three.',
    },
    {
        'question': 'Which field stores the boarding port?',
        'options': ['embarked', 'ticket', 'sibsp'],
        'answer': 'embarked',
        'explanation': 'Embarked stores a port code.',
    },
    {
        'question': 'What does sibsp count?',
        'options': ['Siblings and spouses aboard', 'Parents and children aboard', 'Cabin numbers'],
        'answer': 'Siblings and spouses aboard',
        'explanation': 'sibsp counts siblings and spouses.',
    },
    {
        'question': 'What does parch count?',
        'options': ['Parents and children aboard', 'Siblings and spouses aboard', 'Passenger classes'],
        'answer': 'Parents and children aboard',
        'explanation': 'parch counts parents and children.',
    },
    {
        'question': 'Which field stores ticket identifiers?',
        'options': ['ticket', 'age', 'survived'],
        'answer': 'ticket',
        'explanation': 'ticket stores ticket labels.',
    },
    {
        'question': 'Which field stores cabin identifiers?',
        'options': ['cabin', 'fare', 'sex'],
        'answer': 'cabin',
        'explanation': 'cabin stores cabin labels where known.',
    },
    {
        'question': 'Which field stores age?',
        'options': ['age', 'name', 'pclass'],
        'answer': 'age',
        'explanation': 'age stores a number or NULL.',
    },
    {
        'question': 'Which field identifies a source passenger?',
        'options': ['passengerid', 'embarked', 'fare'],
        'answer': 'passengerid',
        'explanation': 'passengerid is the source row identifier.',
    },
    {
        'question': 'Why should missing age not become zero automatically?',
        'options': ['Zero pretends the age is known', 'Zero means survived', 'SQL cannot store zero'],
        'answer': 'Zero pretends the age is known',
        'explanation': 'Missing values should not be changed without a reason.',
    },
    {
        'question': 'How do you sort fares high to low?',
        'options': ['ORDER BY fare DESC', 'GROUP BY fare', 'WHERE fare NULL'],
        'answer': 'ORDER BY fare DESC',
        'explanation': 'DESC sorts in descending order.',
    },
    {
        'question': 'How do you sort fares low to high?',
        'options': ['ORDER BY fare ASC', 'HAVING fare', 'LIMIT fare'],
        'answer': 'ORDER BY fare ASC',
        'explanation': 'ASC sorts in ascending order.',
    },
    {
        'question': 'What does a primary key do?',
        'options': ['Uniquely identifies a row', 'Stores many rows in one cell', 'Makes every value blank'],
        'answer': 'Uniquely identifies a row',
        'explanation': 'A primary key identifies one record.',
    },
    {
        'question': 'What does a foreign key do?',
        'options': ['Links related records', 'Sorts a query', 'Counts NULL values'],
        'answer': 'Links related records',
        'explanation': 'A foreign key connects rows between tables.',
    },
    {
        'question': 'What does SUM(survived) count?',
        'options': ['Number of survivors', 'Average age', 'Passenger class'],
        'answer': 'Number of survivors',
        'explanation': 'Adding zero and one values counts the ones.',
    },
    {
        'question': 'What is a staging table for?',
        'options': ['A place to inspect imported data', 'A web browser', 'A password holder'],
        'answer': 'A place to inspect imported data',
        'explanation': 'A staging table is a first stop for imported rows.',
    },
    {
        'question': 'Which aggregate counts non-missing values in a column?',
        'options': ['COUNT(column)', 'ORDER BY', 'LIMIT'],
        'answer': 'COUNT(column)',
        'explanation': 'COUNT(column) skips NULL values.',
    },
    {
        'question': 'Which psql command changes databases?',
        'options': ['\\c database_name', 'USE database_name', 'SWITCH database'],
        'answer': '\\c database_name',
        'explanation': 'The psql command \\c connects to another database.',
    },
    {
        'question': 'Which psql command lists tables?',
        'options': ['\\dt', '\\tables', 'SHOW TABLE'],
        'answer': '\\dt',
        'explanation': '\\dt lists tables in the current database.',
    },
    {
        'question': 'What is a schema?',
        'options': ['A folder for database objects', 'One passenger row', 'A Python package'],
        'answer': 'A folder for database objects',
        'explanation': 'A schema organizes tables inside a database.',
    },
    {
        'question': 'Why use HEADER TRUE when importing CSV?',
        'options': ['It skips the column-name row', 'It deletes a passenger', 'It changes the database'],
        'answer': 'It skips the column-name row',
        'explanation': 'HEADER TRUE skips the CSV header.',
    },
    {
        'question': 'What does a CHECK constraint do?',
        'options': ['Rejects values that break a rule', 'Sorts rows', 'Opens a webpage'],
        'answer': 'Rejects values that break a rule',
        'explanation': 'CHECK constraints protect data quality.',
    },
]
COLUMN_GUIDE = [
    {
        'column': 'name',
        'meaning': 'Passenger name and title',
    },
    {
        'column': 'sex',
        'meaning': 'Recorded sex label',
    },
    {
        'column': 'age',
        'meaning': 'Age; some values are missing',
    },
    {
        'column': 'sibsp',
        'meaning': 'Siblings and spouses aboard',
    },
    {
        'column': 'parch',
        'meaning': 'Parents and children aboard',
    },
    {
        'column': 'embarked',
        'meaning': 'Boarding port code',
    },
    {
        'column': 'ticket',
        'meaning': 'Ticket identifier',
    },
    {
        'column': 'fare',
        'meaning': 'Ticket fare',
    },
    {
        'column': 'cabin',
        'meaning': 'Cabin identifier; many are missing',
    },
    {
        'column': 'passengerid',
        'meaning': 'Passenger number in source file',
    },
    {
        'column': 'pclass',
        'meaning': 'Passenger class: 1, 2, or 3',
    },
    {
        'column': 'survived',
        'meaning': '1 means yes; 0 means no',
    },
]

# Assignment version and line-count target.
APP_VERSION = "1.0"
REQUIRED_APP_LINE_COUNT = 1000
dashboard, explorer, sql_lab, quiz_tab, guide, about = st.tabs(
    ["Dashboard", "Data Explorer", "SQL Library", "Quiz", "Column Guide", "About"]
)

with dashboard:
    st.subheader("The passenger list at a glance")
    a, b, c, d = st.columns(4)
    a.metric("Passenger records", f"{total_passengers:,}")
    b.metric("Survived", f"{survivors:,}")
    c.metric("Did not survive", f"{total_passengers - survivors:,}")
    d.metric("Survival rate", f"{survival_percent:.1f}%")

    left, right = st.columns(2)
    with left:
        st.markdown("#### Passenger class sizes")
        class_counts = value_counts(passengers, "pclass")
        biggest = max(class_counts.values(), default=0)
        for name in sorted(class_counts):
            draw_bar("Class " + name, class_counts[name], biggest)
    with right:
        st.markdown("#### Survival results")
        results = value_counts(passengers, "survived")
        biggest = max(results.values(), default=0)
        labels = {"0": "Did not survive", "1": "Survived", "(missing)": "Missing"}
        for name in sorted(results):
            draw_bar(labels.get(name, name), results[name], biggest)

    st.markdown("#### Survival by passenger class")
    try:
        display_table(run_query(
            f"SELECT pclass, survived, COUNT(*) AS passenger_count "
            f"FROM {TABLE} GROUP BY pclass, survived ORDER BY pclass, survived"
        ))
    except Exception as error:
        st.info(f"Summary not available: {error}")

    st.markdown("#### A few missing-value counts")
    missing = []
    for column in ("age", "embarked", "cabin"):
        missing.append({
            "column": column,
            "missing_rows": sum(1 for row in passengers if row.get(column) is None),
        })
    display_table(missing)

with explorer:
    st.subheader("Find passengers")
    classes = sorted({row.get("pclass") for row in passengers if row.get("pclass") is not None})
    sexes = sorted({row.get("sex") for row in passengers if row.get("sex") is not None})
    outcomes = sorted({row.get("survived") for row in passengers if row.get("survived") is not None})
    chosen_classes = st.multiselect("Class", classes, default=classes)
    chosen_sexes = st.multiselect("Sex", sexes, default=sexes)
    chosen_outcomes = st.multiselect("Survival result", outcomes, default=outcomes)
    name_fragment = st.text_input("Name contains", "").strip().lower()
    found = []
    for row in passengers:
        if row.get("pclass") not in chosen_classes:
            continue
        if row.get("sex") not in chosen_sexes:
            continue
        if row.get("survived") not in chosen_outcomes:
            continue
        if name_fragment and name_fragment not in str(row.get("name", "")).lower():
            continue
        found.append(row)
    st.write(f"Found **{len(found):,}** passenger(s).")
    display_table(found)
    st.download_button(
        "Download matching rows as CSV",
        data=create_csv(found),
        file_name="titanic_passengers.csv",
        mime="text/csv",
        disabled=not found,
    )

with sql_lab:
    st.subheader("SQL practice library")
    st.write("Select a prepared read-only question and run it on the staging table.")
    lesson_names = [item["title"] for item in SQL_LESSONS]
    selected_name = st.selectbox("Choose a lesson", lesson_names)
    lesson = next(item for item in SQL_LESSONS if item["title"] == selected_name)
    st.markdown(f"**Topic:** {lesson['topic']}")
    st.write(lesson["description"])
    st.code(lesson["sql"], language="sql")
    if st.button("Run this SQL example"):
        try:
            result = run_query(lesson["sql"])
            st.success(f"Returned {len(result):,} row(s).")
            display_table(result)
        except Exception as error:
            st.error("This prepared query did not run.")
            st.caption(str(error))

with quiz_tab:
    st.subheader("SQL and Titanic quiz")
    quiz_names = [item["question"] for item in QUIZ_QUESTIONS]
    chosen_question = st.selectbox("Choose a question", quiz_names)
    quiz = next(item for item in QUIZ_QUESTIONS if item["question"] == chosen_question)
    choice = st.radio("Your answer", quiz["options"], key="quiz_choice")
    if st.button("Check answer"):
        if choice == quiz["answer"]:
            st.success("Correct! " + quiz["explanation"])
        else:
            st.info("Not quite. " + quiz["explanation"])

with guide:
    st.subheader("Column guide")
    st.write("Each row in the CSV is one passenger.")
    display_table(COLUMN_GUIDE)
    st.info("Missing values stay blank; they are not changed to zero.")

with about:
    st.subheader("Project workflow")
    st.markdown(
        "1. The CSV contains the passenger list.\\n"
        "2. PostgreSQL stores the rows in a staging table.\\n"
        "3. SQL filters, groups, counts, and summarizes the rows.\\n"
        "4. Python connects the webpage to PostgreSQL.\\n"
        "5. Streamlit displays the interactive project."
    )
    st.write(f"Rows loaded: {total_passengers:,}")
    st.write(f"SQL lessons included: {len(SQL_LESSONS):,}")
    st.write(f"Quiz questions included: {len(QUIZ_QUESTIONS):,}")
    st.caption("The app reads the staging table so it can use the original CSV columns.")

