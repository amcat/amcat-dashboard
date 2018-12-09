define(function () {

    class ValidationError extends Error {
    }

    function _validateFilter(val) {

        // todo: better validation. Ideally we'd want it to be able to parse the whole query grammar.

        let c = 0;
        let state = [];

        function start() {
            switch (val[c]) {
                case '(':
                    state.push(subclauseStart);
                    break;
                case '"':
                    state.push(literal);
                    break;
                case '#':
                case '|':
                    throw new ValidationError("Invalid character (# or |)");
                case ')':
                    throw new ValidationError("Unbalanced parentheses");
            }
            c++;
        }

        function literal() {
            switch (val[c]) {
                //case '\\': // apparently amcat doesn't like escapes. A quote is a quote.
                //    c += 2;
                //    return;
                case '"':
                    state.pop();
                    break;
            }
            c++;
        }
        function subclauseStart() {
            switch (val[c]) {
                case '(':
                    state.push(subclauseBody);
                    state.push(subclauseStart);
                    break;
                case '"':
                    state.push(literal);
                    break;
                case '#':
                case '|':
                    throw new ValidationError("Invalid character (# or |)");
                case ')':
                    throw new ValidationError("Empty subclause");
                case ' ':
                    break;
                default:
                    state.push(subclauseBody);
            }
            c++;
        }
        function subclauseBody() {
            switch (val[c]) {
                case '(':
                    state.push(subclauseStart);
                    break;
                case '"':
                    state.push(literal);
                    break;
                case '#':
                case '|':
                    throw new ValidationError("Invalid character (# or |)");
                case ')':
                    state.pop();
                    state.pop();
                    break;
            }
            c++;
        }


        state.push(start);
        while (c < val.length) {
            if (state.length < 1) {
                throw new ValidationError("The start state is missing. This probably isn't your fault.")
            }
            state[state.length - 1]();
        }

        // try to balance parentheses
        while (state.length > 1) {
            if (state[state.length - 1] === subclauseBody) {
                val += ')';
                state.pop();
                state.pop();
            }
            else {
                break;
            }
        }
        if (state[state.length - 1] === literal) {
            throw new ValidationError('Unbalanced double quotes (")');
        }
        else if (state[state.length - 1] === subclauseStart) {
            throw new ValidationError('Unbalanced parentheses');
        }
        else if (state.length > 1){
            throw new ValidationError('Invalid syntax');
        }
        return val;
    }

    function validateFilter(event ,filterInput) {
        filterInput.value = filterInput.value.trim();
        try {
            filterInput.value = _validateFilter(filterInput.value);
        }
        catch (err) {
            event.preventDefault();
            if (!(err instanceof ValidationError))
                throw err;
            filterInput.setCustomValidity(err);
        }
    }
    return {ValidationError, validateFilter}
});