{% import 'common.rst' as common %}

{% if is_interface -%}
.. js:interface:: {{ name }}{{ type_params }}{{ params }}
{%- else -%}
.. js:class:: {{ name }}{{ type_params }}{{ params }}
{%- endif %}

   {{ common.deprecated(deprecated)|indent(3) }}

   {% if class_comment -%}
     {{ class_comment|indent(3) }}
   {%- endif %}

   {% if is_abstract -%}
     *abstract*
   {%- endif %}

   {{ common.exported_from(exported_from)|indent(3) }}

   {% if supers -%}
     **Extends:**
       {% for super in supers -%}
         - {{ super }}
       {% endfor %}
   {%- endif %}

   {% if interfaces -%}
     **Implements:**
       {% for interface in interfaces -%}
         - {{ interface }}
       {% endfor %}
   {%- endif %}

   {% if constructor_comment -%}
     {{ constructor_comment|indent(3) }}
   {%- endif %}

   {{ common.fields(fields) | indent(3) }}

   {{ common.examples(examples)|indent(3) }}

   {{ content|indent(3) }}

   {% if members -%}
     {{ members|indent(3) }}
   {%- endif %}

   {{ common.see_also(see_also)|indent(3) }}
