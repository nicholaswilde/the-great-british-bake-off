test_that("all 4 datasets exist and have expected structure", {
  expect_true(exists("seasons"))
  expect_true(exists("bakers"))
  expect_true(exists("episodes"))
  expect_true(exists("performances"))

  tables <- list(
    seasons = seasons,
    bakers = bakers,
    episodes = episodes,
    performances = performances
  )

  for (name in names(tables)) {
    df <- tables[[name]]
    expect_s3_class(df, "data.frame")
    expect_gt(nrow(df), 0)
    expect_gt(ncol(df), 0)
  }
})

test_that("seasons table has series_number integer column", {
  expect_true(is.integer(seasons$series_number))
})

test_that("performances table has boolean flag columns", {
  expect_true(is.logical(performances$hollywood_handshake))
  expect_true(is.logical(performances$did_well))
})
