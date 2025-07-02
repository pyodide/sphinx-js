{% macro deprecated(message) %}
{% if message -%}
.. note::

   Deprecated
   {%- if message is string -%}: {{ message }}{% else %}.{% endif -%}
{%- endif %}
{% endmacro %}

{% macro examples(items) %}
{% for example in items %}

.. admonition:: Example

   {{ example|indent(3) }}
{% endfor %}
{% endmacro %}

{% macro see_also(items) %}
{% if items -%}
.. seealso::

   {% for reference in items -%}
   - :any:`{{ reference }}`
   {% endfor %}
{%- endif %}
{% endmacro %}

{% macro exported_from(pathname) %}
{% if pathname -%}
    *exported from* :js:mod:`{{ pathname.dotted() }}`
{%- endif %}
{% endmacro %}

{% macro fields(items) %}
{% for heads, tail in items -%}
   :{{ heads|join(' ') }}: {{ tail }}
{% endfor %}
{% endmacro %}
