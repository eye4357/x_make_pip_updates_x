from x_cls_make_pip_x import x_cls_make_pip_x

if __name__ == "__main__":
    # Minimal example: install default packages
    x_cls_make_pip_x().batch_install([
        "x_make_markdown_x",
        "x_make_pypi_x",
        "x_make_github_clones_x"
    ])
