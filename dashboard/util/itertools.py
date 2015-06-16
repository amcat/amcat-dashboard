def split(condition, seq):
    conform = []
    do_not_conform = []

    for x in seq:
        if condition(x):
            conform.append(x)
        else:
            do_not_conform.append(x)

    return conform, do_not_conform
