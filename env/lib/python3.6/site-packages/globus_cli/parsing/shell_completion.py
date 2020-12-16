import click

# pulled by running `_GLOBUS_COMPLETE=source globus` in a bash shell
BASH_SHELL_COMPLETER = r"""_globus_completion() {
    local IFS=$'
'
    COMPREPLY=( $( env COMP_WORDS="${COMP_WORDS[*]}" \
                   COMP_CWORD=$COMP_CWORD \
                   _GLOBUS_COMPLETE=complete $1 ) )
    return 0
}

_globus_completionetup() {
    local COMPLETION_OPTIONS=""
    local BASH_VERSION_ARR=(${BASH_VERSION//./ })
    # Only BASH version 4.4 and later have the nosort option.
    if [ ${BASH_VERSION_ARR[0]} -gt 4 ] || (
            [ ${BASH_VERSION_ARR[0]} -eq 4 ] && [ ${BASH_VERSION_ARR[1]} -ge 4 ]); then
        COMPLETION_OPTIONS="-o nosort"
    fi

    complete $COMPLETION_OPTIONS -F _globus_completion globus
}

_globus_completionetup;"""

# pulled by running `_GLOBUS_COMPLETE=source_zsh globus` in a zsh shell
ZSH_SHELL_COMPLETER = r"""_globus_completion() {
    local -a completions
    local -a completions_with_descriptions
    local -a response
    response=("${(@f)$( env COMP_WORDS="${words[*]}" \
                        COMP_CWORD=$((CURRENT-1)) \
                        _GLOBUS_COMPLETE="complete_zsh" \
                        globus )}")

    for key descr in ${(kv)response}; do
      if [[ "$descr" == "_" ]]; then
          completions+=("$key")
      else
          completions_with_descriptions+=("$key":"$descr")
      fi
    done

    if [ -n "$completions_with_descriptions" ]; then
        _describe -V unsorted completions_with_descriptions -U -Q
    fi

    if [ -n "$completions" ]; then
        compadd -U -V unsorted -Q -a completions
    fi
    compstate[insert]="automenu"
}

compdef _globus_completion globus;"""


def print_completer_option(f):
    def callback(ctx, param, value):
        if not value or ctx.resilient_parsing:
            return
        if value == "BASH":
            click.echo(BASH_SHELL_COMPLETER)
        elif value == "ZSH":
            click.echo(ZSH_SHELL_COMPLETER)
        else:
            raise ValueError("Unsupported shell completion")
        click.get_current_context().exit(0)

    f = click.option(
        "--completer",
        "--bash-completer",
        hidden=True,
        is_eager=True,
        expose_value=False,
        flag_value="BASH",
        callback=callback,
    )(f)
    f = click.option(
        "--zsh-completer",
        hidden=True,
        is_eager=True,
        expose_value=False,
        flag_value="ZSH",
        callback=callback,
    )(f)
    return f
