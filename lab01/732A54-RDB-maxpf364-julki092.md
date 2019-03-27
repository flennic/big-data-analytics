# Task 1)

SELECT * FROM jbemployee

# Task 2)

SELECT name FROM jbdept ORDER BY name

# Task 3)

SELECT name FROM jbparts WHERE qoh = 0 ORDER BY name

# Task 4)

SELECT name FROM jbemployee WHERE salary >= 9000 AND salary <= 10000 ORDER BY name

# Task 5)

SELECT *, (startyear-birthyear) AS "Age When Started" FROM jbemployee

# Task 6)

SELECT * FROM jbemployee WHERE name LIKE "%son"

# Task 7)

SELECT * FROM jbitem WHERE supplier IN (SELECT id from jbsupplier WHERE name = "Fisher-Price")

# Task 8)

SELECT * FROM jbitem INNER JOIN jbsupplier ON jbitem.supplier = jbsupplier.id WHERE jbsupplier.name = "Fisher-Price"

# Task 9)

SELECT * FROM jbcity WHERE jbcity.id IN (SELECT city FROM jbsupplier)

# Task 10)

SELECT name, color FROM jbparts WHERE weight > (SELECT weight FROM jbparts WHERE name = "card reader")

# Task 11)

SELECT parts1.name, parts1.color FROM jbparts AS parts1, jbparts AS parts2 WHERE parts2.name = "card reader" AND parts1.weight > parts2.weight

# Task 12)

SELECT AVG(weight) FROM jbparts WHERE color = 'black'

# Task 13)

SELECT jbsupplier.name, SUM(js.quan * jp.weight) AS total_weight FROM jbsupplier
  LEFT JOIN jbcity jc ON jbsupplier.city = jc.id
  LEFT JOIN jbsupply js ON jbsupplier.id = js.supplier
  LEFT JOIN jbparts jp on js.part = jp.id
  WHERE  jc.state = 'MASS'
  GROUP BY jbsupplier.id

# Task 14)

CREATE TABLE jbitem_custom (
    id INT,
    name VARCHAR(20),
    dept INT NOT NULL,
    price INT,
    qoh INT UNSIGNED,
    supplier INT,
    CONSTRAINT pk_item PRIMARY KEY(id),
    CONSTRAINT dept FOREIGN KEY(dept) REFERENCES jbdept(id),
    CONSTRAINT supplier FOREIGN KEY(supplier) REFERENCES jbsupplier(id));


INSERT INTO jbitem_custom (id, name, dept, price, qoh, supplier)
  SELECT ji.id, ji.name, ji.dept, ji.price, ji.qoh, ji.supplier
  FROM jbitem AS ji WHERE ji.price < (SELECT AVG(jbitem.price) FROM jbitem)
