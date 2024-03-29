# Changelog

## v0.8.0 - 2023-08-03

-   Fixed `replace_metavar` erroneously treating `\` as regex escapes
-   Added `repeat_pattern()`
-   Added `reflow_text()`
-   Added `to_snake_case()`
-   Added `to_pascal_case()`
-   Added `remove_duplicates()`

## v0.7.1 - 2023-07-17

-   Fixed `copy_file()` not following symlinks

## v0.7.0 - 2022-09-05

-   Added `none` filter to `enumerate_files()`
-   Added `tabify()`
-   Added `untabify()`
-   Added `reindent()`

## v0.6.1 - 2022-08-13

-   Fixed typos in `print_exception()`

## v0.6.0 - 2022-05-08

-   Added `coerce_collection()`
-   Added `coerce_path()`
-   Added `enumerate_files()`
-   Added `enumerate_directories()`
-   Added `check` argument to `run_python_script()`
-   Added function return type annotations

## v0.5.0 - 2021-09-11

-   Added `replace_metavar()`

## v0.4.0 - 2021-04-22

-   Fixed `get_all_files()` filtering on full paths instead of filenames only
-   Fixed `print_exception()` output missing a newline

## v0.3.0 - 2021-04-20

-   Decoupled begin and end logger for `ScopeTimer`

## v0.2.0 - 2021-04-18

-   Fixed incorrect boolean logic in `assert_existing_XXXXX()`
