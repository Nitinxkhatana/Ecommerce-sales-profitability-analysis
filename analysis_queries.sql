-- ============================================================================
-- Stage 3 - SQL analysis demonstration on the Superstore dataset
-- Database: data/ecommerce.db    Table: superstore (9,993 rows)
-- All values returned are computed from the real cleaned dataset.
-- ============================================================================


-- ============================================================================
-- SECTION 1 - SELECT / WHERE / ORDER BY / LIMIT
-- ============================================================================

-- Q1 SELECT with LIMIT: first 5 order lines (basic projection + sorting)
SELECT Order_ID, Order_Date, Customer_Name, Region, Product_Name, Sales, Profit
FROM superstore
ORDER BY Order_Date ASC, Order_ID ASC
LIMIT 5;

-- Q2 WHERE + ORDER BY: the 10 most profitable order lines of 2017
SELECT Order_ID, Order_Date, Product_Name, Sales, Discount, Profit
FROM superstore
WHERE Order_Year = 2017 AND Profit > 0
ORDER BY Profit DESC
LIMIT 10;

-- Q3 WHERE with multiple conditions: loss-making Furniture lines
SELECT Order_ID, Product_Name, Sales, Discount, Profit
FROM superstore
WHERE Category = 'Furniture' AND Profit < 0
ORDER BY Profit ASC
LIMIT 10;

-- ============================================================================
-- SECTION 2 - GROUP BY / AGGREGATES
-- ============================================================================

-- Q4 Aggregates by category: revenue, profit, avg profit margin, line count
SELECT Category,
       COUNT(*)                        AS Line_Items,
       ROUND(SUM(Sales), 2)            AS Revenue,
       ROUND(SUM(Profit), 2)           AS Profit,
       ROUND(AVG(Profit / Sales) * 100, 1) AS Avg_Margin_Pct
FROM superstore
GROUP BY Category
ORDER BY Profit DESC;

-- Q5 GROUP BY region: key business KPIs per region
SELECT Region,
       COUNT(*)                    AS Line_Items,
       COUNT(DISTINCT Order_ID)    AS Orders,
       ROUND(SUM(Sales), 2)        AS Revenue,
       ROUND(SUM(Profit), 2)       AS Profit,
       ROUND(AVG(Sales), 2)        AS Avg_Line_Value
FROM superstore
GROUP BY Region
ORDER BY Revenue DESC;

-- Q6 GROUP BY with HAVING: customers generating over 5,000 in lifetime revenue
SELECT Customer_Name,
       COUNT(DISTINCT Order_ID) AS Orders,
       ROUND(SUM(Sales), 2)     AS Lifetime_Revenue
FROM superstore
GROUP BY Customer_Name
HAVING SUM(Sales) > 5000
ORDER BY Lifetime_Revenue DESC
LIMIT 10;

-- ============================================================================
-- SECTION 3 - JOINS (superstore joined to its own real aggregates)
-- ============================================================================

-- Q7 INNER JOIN: 2017 order lines of repeat customers only.
--    The joined table is a real aggregate view built from this data
--    (customers with more than 10 orders lifetime).
SELECT s.Order_ID,
       s.Customer_Name,
       s.Product_Name,
       s.Sales,
       s.Profit,
       c.Total_Orders
FROM superstore AS s
INNER JOIN (
    SELECT Customer_ID,
           COUNT(DISTINCT Order_ID) AS Total_Orders
    FROM superstore
    GROUP BY Customer_ID
    HAVING COUNT(DISTINCT Order_ID) > 10
) AS c
    ON s.Customer_ID = c.Customer_ID
WHERE s.Order_Year = 2017
ORDER BY s.Sales DESC
LIMIT 10;

-- Q8 SELF/AGGREGATE JOIN: how much do the largest states contribute to
--    their region's total revenue (state revenue joined to region revenue)
SELECT Region,
       State,
       ROUND(State_Revenue, 2)  AS State_Revenue,
       ROUND(Region_Revenue, 2) AS Region_Revenue,
       ROUND(State_Revenue * 100.0 / Region_Revenue, 1) AS State_Share_Pct
FROM (
    SELECT r.Region,
           r.State,
           r.State_Revenue,
           s.Region_Revenue
    FROM (
        SELECT Region, State, SUM(Sales) AS State_Revenue
        FROM superstore
        GROUP BY Region, State
    ) AS r
    JOIN (
        SELECT Region, SUM(Sales) AS Region_Revenue
        FROM superstore
        GROUP BY Region
    ) AS s
        ON r.Region = s.Region
)
ORDER BY State_Share_Pct DESC
LIMIT 5;

-- ============================================================================
-- SECTION 4 - SUBQUERIES
-- ============================================================================

-- Q9 Scalar subquery: order lines with sales above the overall average line value
SELECT COUNT(*)                AS Above_avg_lines,
       ROUND(AVG(Sales), 2)    AS Avg_sales_above,
       ROUND(AVG(Profit), 2)   AS Avg_profit_above
FROM superstore
WHERE Sales > (SELECT AVG(Sales) FROM superstore);

-- Q10 Subquery in FROM: monthly revenue trend with month-over-month row numbers
SELECT Year_Month, Revenue
FROM (
    SELECT Year_Month, ROUND(SUM(Sales), 2) AS Revenue
    FROM superstore
    GROUP BY Year_Month
)
ORDER BY Year_Month ASC
LIMIT 12;

-- Q11 Correlated subquery: for each sub-category, lines with margin exceeding
--     that sub-category's own average margin
SELECT Sub_Category,
       COUNT(*) AS Lines_Above_Own_Avg
FROM superstore AS s
WHERE (s.Profit / s.Sales) > (
    SELECT AVG(s2.Profit / s2.Sales)
    FROM superstore AS s2
    WHERE s2.Sub_Category = s.Sub_Category
)
GROUP BY Sub_Category
ORDER BY Lines_Above_Own_Avg DESC;

-- ============================================================================
-- SECTION 5 - CASE
-- ============================================================================

-- Q12 CASE: classify every line item into a profit band and count bands by region
SELECT Region,
       SUM(CASE WHEN Profit < 0 THEN 1 ELSE 0 END)            AS Loss_Lines,
       SUM(CASE WHEN Profit = 0 THEN 1 ELSE 0 END)            AS BreakEven_Lines,
       SUM(CASE WHEN Profit > 0 AND Profit < 100 THEN 1 ELSE 0 END)  AS Profitable_LT100_Lines,
       SUM(CASE WHEN Profit >= 100 THEN 1 ELSE 0 END)         AS Profitable_GE100_Lines
FROM superstore
GROUP BY Region
ORDER BY Loss_Lines DESC;

-- Q13 CASE inside aggregate: discount intensity buckets and their economics
SELECT CASE
           WHEN Discount = 0   THEN 'No discount'
           WHEN Discount < 0.2 THEN 'Light  (0-20%)'
           WHEN Discount < 0.5 THEN 'Heavy  (20-50%)'
           ELSE 'Extreme (>50%)'
       END AS Discount_Band,
       COUNT(*)                          AS Line_Items,
       ROUND(SUM(Sales), 2)              AS Revenue,
       ROUND(SUM(Profit), 2)             AS Profit,
       ROUND(AVG(Profit / Sales) * 100, 1) AS Avg_Margin_Pct
FROM superstore
GROUP BY Discount_Band
ORDER BY Avg_Margin_Pct DESC;
