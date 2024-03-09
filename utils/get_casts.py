import os
from google.cloud import bigquery

client = bigquery.Client()


def get_casts(channel=None, date=None):
    if not channel:
        raise "No channel provided"

    sql = generate_sql(channel=channel, date=date)

    """
    TODO: cache results of similar queries
          this will likely require intentionally timeboxing queries in some way :thinking:
    """

    query = client.query(sql)
    rows = query.result()

    return [r for r in rows]


def generate_sql(channel=None, date=None):
    if not channel:
        raise "Missing params for generating SQL"

    """
    TODO: reconfigure this a bit to have better limits :thinking:
          OR force everything to be by date
    """

    return f"""

WITH
  root_casts AS (
    SELECT
      c.timestamp,
      c.hash,
      JSON_VALUE(p.data, '$.username') AS username,
      CONCAT('https://warpcast.com/', JSON_VALUE(p.data, '$.username'), "/", SUBSTR(c.hash, 0, 10)) AS url,
      '' AS parent_cast_hash,
      c.text,
      (
        SELECT
          COUNT(*)
        FROM
          `glossy-odyssey-366820.farcaster.reactions`
        WHERE
          target_cast_hash = c.hash
      ) as reaction_count
    FROM
      `glossy-odyssey-366820.farcaster.casts` c
    LEFT JOIN
      `glossy-odyssey-366820.farcaster.profiles` p
    ON
      c.fid = p.fid
    WHERE
      parent_cast_url = '{channel}'
      AND JSON_VALUE(p.data, '$.username') IS NOT NULL
      {f"AND EXTRACT(DATE from c.timestamp) = '{date}'" if date else ""}
  )
SELECT
  *
FROM
  root_casts
UNION ALL (
  SELECT
    c.timestamp,
    c.hash,
    JSON_VALUE(p.data, '$.username') AS username,
    CONCAT('https://warpcast.com/', JSON_VALUE(p.data, '$.username'), "/", SUBSTR(c.hash, 0, 10)) AS url,
    c.parent_cast_hash,
    c.text,
    (
      SELECT
        COUNT(*)
      FROM
        `glossy-odyssey-366820.farcaster.reactions`
      WHERE
        target_cast_hash = c.hash
    ) as reaction_count
  FROM
    `glossy-odyssey-366820.farcaster.casts` c
  LEFT JOIN
    `glossy-odyssey-366820.farcaster.profiles` p
  ON
    c.fid = p.fid
  WHERE
    c.parent_cast_hash IN (
      SELECT
        rc.hash
      FROM
        root_casts rc)
      AND JSON_VALUE(p.data, '$.username') IS NOT NULL
    )
ORDER BY
  reaction_count DESC
LIMIT 50
  """
