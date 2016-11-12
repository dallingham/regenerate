/*----------------------------------------------------------------------------
 *
 * {{project.name}} register package
 *
 * Generated: {{current_date}}
 *
 *----------------------------------------------------------------------------
 */

`include "uvm_macros.svh"

package {{project.short_name|lower}}_reg_pkg;

   import uvm_pkg::*;

   /*
    * Controls the handling of the volatile bit. By default, we try to adhere to
    * the strict definition of UVM - any register that has the potential of
    * changing between reads should be marked as volatile. This does impact some
    * usages of the uvm_reg.mirror(UVM_CHECK) function. So if s_relaxed_volitile
    * is set to a 1, then only registers explicity marked as volatile in regenerate
    * will be identified as volatile. Fields that have an input signal that can
    * change the value will not. In this case, it is the responsibility of the user
    * to manage this potential volatility on thier own.
    */
   bit s_relaxed_volatile = 1'b0;

{% for db in dblist %}

  {%- if db.coverage %}
   class {{db.set_name|lower}}_reg_access_wrapper extends uvm_object;

      `uvm_object_utils({{db.set_name|lower}}_reg_access_wrapper)

      static int s_num = 0;

      covergroup cov_addr(string name) with function sample(uvm_reg_addr_t addr, bit is_read);

         option.per_instance = 1;
         option.name = name;

         READ_ADDR: coverpoint addr iff (is_read) {
            {% for register in db.get_all_registers() %}
	      {% if register.do_not_cover == False %}
           bins r_{{register.token|lower}} = { 'h{{ '%x' | format(register.address) }} };
	      {% endif %}
            {% endfor %}
         }

         WRITE_ADDR: coverpoint addr iff (!is_read) {
            {% for register in db.get_all_registers() %}
              {% if register.is_completely_read_only() == False %}
  	        {% if register.do_not_cover == False %}
           bins r_{{register.token|lower}} = { 'h{{ '%x' | format(register.address) }} };
                {% endif %}
              {% endif %}
            {% endfor %}
         }

      endgroup : cov_addr

      function new(string name = "{{db.set_name|lower}}_reg_access_wrapper");
         cov_addr = new($sformatf("%s_%0d", name, s_num++));
      endfunction : new

      function void sample(uvm_reg_addr_t offset, bit is_read);
         cov_addr.sample(offset, is_read);
      endfunction: sample

   endclass : {{db.set_name|lower}}_reg_access_wrapper
  {%- endif -%}      

  {% for register in db.get_all_registers() %}
    {% if register.ram_size %}
      {% set num_bytes = (register.width / 8)| int %}
   class mem_{{db.set_name|lower}}_{{register.token|lower}} extends uvm_mem;

      `uvm_object_utils(mem_{{db.set_name|lower}}_{{register.token|lower}})

      function new (string name = "mem_{{db.set_name|lower}}_{{register.token|lower}}");
         super.new(name, {{(register.ram_size / num_bytes)|int}}, {{register.width}}, "RW", build_coverage(UVM_NO_COVERAGE));
      endfunction : new

   endclass : mem_{{db.set_name|lower}}_{{register.token|lower}}

    {% else %}

   class reg_{{db.set_name|lower}}_{{register.token|lower}} extends uvm_reg;

      `uvm_object_utils(reg_{{db.set_name|lower}}_{{register.token|lower}})

      // Fields
     {% for field in register.get_bit_fields() %}
       {% if field.can_randomize %}
      rand uvm_reg_field {{fix_name(field)}};
       {% else %}
      uvm_reg_field {{fix_name(field)}};
       {% endif %}
     {% endfor %}

     {%- if db.coverage %}      
      // Locals for coverage
      local uvm_reg_data_t m_data;
      local uvm_reg_data_t m_be;
      local bit            m_is_read;
     {%- endif -%}      
     {% for field  in register.get_bit_fields() %}
     {%   if field.can_randomize and field.values|length > 0 %}
      constraint con_{{fix_name(field)}} {
         {{fix_name(field)}}.value inside { {% for value in field.values %}{{field.width}}'h{{value[0]}}{% if not loop.last %}, {% endif %}{% endfor %} };
      }
     {%   endif %}

     {%- endfor -%}
     {% if db.coverage %}      
       {% if register.get_bit_fields_with_values() | length > 0 %}
	 {% if register.do_not_cover == False %}
      covergroup cov_fields;
         option.per_instance = 1;
           {% for field in register.get_bit_fields_with_values() %}
         {{fix_name(field)|upper}}: coverpoint m_data[{{field.msb}}:{{field.lsb}}] {
               {% for value in field.values %}
            bins {{fix_name(field)}}_{{value[0]}} = {'h{{value[0]}} };
               {% endfor %}
         }
           {% endfor %}
         {% endif %}
      endgroup : cov_fields

      covergroup cov_bits;
         option.per_instance = 1;
         {% for field in register.get_bit_fields() %}
  	   {% if register.do_not_cover == False %}
             {% for i in range(field.lsb, field.msb+1) %}
               {% if field.is_read_only() == 0 %}
         {{fix_name(field)|upper}}_W{{i}}: coverpoint (m_data[{{i}}]) iff (!m_is_read && m_be[{{(i/8)|int}}]);
               {% endif %}
               {% if field.is_read_only() and field.is_constant() %}
         {{fix_name(field)|upper}}_R{{i}}: coverpoint (m_data[{{i}}]) iff (m_is_read) {bins ro_{{i}} = { {{field.reset_value_bit(i - field.lsb)}} }; }
               {% else %}
         {{fix_name(field)|upper}}_R{{i}}: coverpoint (m_data[{{i}}]) iff (m_is_read);
               {% endif %}
             {% endfor %}
           {% endif %}
         {% endfor %}
      endgroup : cov_bits
       {% endif %}      
     {% endif %}

      function new(string name = "{{register.token|lower}}");
         super.new(name, {{register.width}}, build_coverage(UVM_CVR_FIELD_VALS + UVM_CVR_REG_BITS));
     {% if db.coverage and register.do_not_cover == False %}      
       {% if register.get_bit_fields() | length > 0 %}
         if (has_coverage(UVM_CVR_REG_BITS)) begin
            cov_bits = new;
         end
       {% endif %}
       {% if register.get_bit_fields_with_values() | length > 0 %}
         if (has_coverage(UVM_CVR_FIELD_VALS)) begin
            cov_fields = new;
         end
       {% endif %}
     {% endif %}
      endfunction : new

     {% if db.coverage and register.do_not_cover == False %}      
      function void sample(uvm_reg_data_t data, uvm_reg_data_t byte_en,
                           bit is_read, uvm_reg_map map);
         super.sample(data, byte_en, is_read, map);
       {% if register.get_bit_fields() | length > 0 %}
         if (get_coverage(UVM_CVR_REG_BITS)) begin
            m_data    = data;
            m_be      = byte_en;
            m_is_read = is_read;
            cov_bits.sample();
         end
       {% endif %}
       {% if register.get_bit_fields_with_values() | length > 0 %}
         if (get_coverage(UVM_CVR_FIELD_VALS)) begin
            sample_values();
            cov_fields.sample();
         end
       {% endif %}

      endfunction: sample
     {% endif %}
       
      virtual function void build();
     {% for field in register.get_bit_fields() %}
       {% if use_new %}
         {{fix_name(field)}} = new("{{fix_name(field)}}");
       {% else %}
         {{fix_name(field)}} = uvm_reg_field::type_id::create("{{fix_name(field)}}");
       {% endif %}
     {% endfor %}
     {%- for field in register.get_bit_fields() -%}
        {%- if field.volatile %}
          {% set volatile = "1" %}
        {% elif field.input_signal != "" %}
          {% set volatile = "!" + project.short_name|lower + "_reg_pkg::s_relaxed_volatile" %}
        {% else %}
          {% set volatile = "0" %}
        {% endif %}
        {%- set reset = "%d'h%x" | format(field.width, field.reset_value) %}
        {%- set has_reset = 1 %}
        {%- set ind_access = individual_access(field, register) %}
        {%- set access = ACCESS_MAP[field.field_type] %}

         {{fix_name(field)}}.configure(this, {{field.width}}, {{field.lsb}}, "{{access}}", {{volatile}}, {{reset}}, {{has_reset}}, {% if field.can_randomize %}1{% else %}0{% endif %}, {{ind_access}});
     {%- endfor %}

      {% if register.no_reset_test() == True %}
         uvm_resource_db #(bit)::set({"REG::", get_full_name()}, "NO_REG_TESTS", 1, this);
      {% elif register.strict_volatile() %}
         {% if register.loose_volatile() %}
         uvm_resource_db #(bit)::set({"REG::", get_full_name()}, "NO_REG_HW_RESET_TEST", 1, this);
         {% else %}
         if ({{project.short_name|lower}}_reg_pkg::s_relaxed_volatile == 1'b0) begin
            uvm_resource_db #(bit)::set({"REG::", get_full_name()}, "NO_REG_HW_RESET_TEST", 1, this);
         end
         {% endif %}
      {% endif %}
      endfunction : build

   endclass : reg_{{db.set_name|lower}}_{{register.token|lower}}
    {% endif %}
   {% endfor %}
{% endfor %}

{% for db, group, grp_map in db_grp_maps %}
  class {{group.name|lower}}_{{db.set_name|lower}}_reg_blk extends uvm_reg_block;

    `uvm_object_utils({{group.name|lower}}_{{db.set_name|lower}}_reg_blk)

   {% for register in db.get_all_registers() %}
     {% if register.ram_size %}
    mem_{{db.set_name|lower}}_{{register.token|lower}} {{register.token|lower}};
     {% else %}
    reg_{{db.set_name|lower}}_{{register.token|lower}} {{register.token|lower}};
     {% endif %}
   {% endfor %}
   {% for map in grp_map %}
    uvm_reg_map {{map}}_map;
   {% endfor %}
   {% if grp_map|length > 1 %}
     {% for map in grp_map %}
    bit disable_{{map}}_map = 1'b0;
     {% endfor %}
   {% endif %}

   {% if db.coverage %}			       
    {{db.set_name|lower}}_reg_access_wrapper {{db.set_name|lower}}_access_cg;
   {% endif %}

    function new(string name = "{{group.name|lower}}_{{db.set_name|lower}}_reg_blk");
      super.new(name, build_coverage(UVM_CVR_ADDR_MAP));
    endfunction

    virtual protected function uvm_reg_map build_address_map(string map_name, int unsigned width);
       uvm_reg_map rmap;
       if ({{(db.data_bus_width / 8)|int}} > width) begin
          rmap = create_map(map_name, 'h0, width, UVM_LITTLE_ENDIAN);
       end else begin
          rmap = create_map(map_name, 'h0, {{(db.data_bus_width/8)|int}}, UVM_LITTLE_ENDIAN);
       end
    {% for reg in db.get_all_registers() %}
       {% if reg.ram_size %}
       rmap.add_mem({{reg.token|lower}}, 'h{{"%04x" | format(reg.address)}}, "RW");
      {% else %}
       rmap.add_reg({{reg.token|lower}}, 'h{{"%04x" | format(reg.address)}}, "RW");
      {% endif %}
    {%- endfor %}
       return rmap;
    endfunction : build_address_map

    virtual function void build();

{% if db.coverage %}			       
      if (has_coverage(UVM_CVR_ADDR_MAP)) begin
  {% if use_new %}
        {{db.set_name|lower}}_access_cg = new("{{db.set_name|lower}}_access_cg");
  {% else %}
        {{db.set_name|lower}}_access_cg = {{db.set_name|lower}}_reg_access_wrapper::type_id::create("{{db.set_name|lower}}_access_cg");
  {% endif %}
      end
{% endif %}

   {% for register in db.get_all_registers() %}
      {% if register.ram_size %}
        {% if use_new %}
      {{register.token|lower}} = new("{{register.token|lower}}");
        {% else %}
      {{register.token|lower}} = mem_{{db.set_name|lower}}_{{register.token|lower}}::type_id::create("{{register.token|lower}}");
        {% endif %}
      {{register.token|lower}}.configure(this);
      {% else %}
        {% if use_new %}
      {{register.token|lower}} = new("{{register.token|lower}}");
        {% else %}
      {{register.token|lower}} = reg_{{db.set_name|lower}}_{{register.token|lower}}::type_id::create("{{register.token|lower}}");
        {% endif %}
      {{register.token|lower}}.configure(this);
      {{register.token|lower}}.build();
      {% for field in register.get_bit_fields() %}
      {{register.token|lower}}.add_hdl_path_slice("r{{'%02x' | format(register.address)}}_{{fix_name(field)}}", {{field.lsb}}, {{field.width}});
      {% endfor %}
      {% endif %}
   {% endfor %}

   {% if grp_map|length == 1 %}
     {% for map in grp_map %}
      {{map}}_map = build_address_map("{{map}}_map", {{project.get_address_width(map)}});
     {% endfor %}
   {% else %}
     {% for map in grp_map %}
      if (!disable_{{map}}_map) {{map}}_map = build_address_map("{{map}}_map", {{project.get_address_width(map)}});
     {% endfor %}
   {% endif %}

    endfunction : build

   {% if db.coverage %}	
    function void sample(uvm_reg_addr_t offset, bit is_read, uvm_reg_map  map);
       if (get_coverage(UVM_CVR_ADDR_MAP)) begin
          {{db.set_name|lower}}_access_cg.sample(offset, is_read);
       end
    endfunction: sample
   {% endif %}

  endclass : {{group.name|lower}}_{{db.set_name|lower}}_reg_blk

{% endfor %}

{% for group in group_maps %}

  class {{group.name|lower}}_grp_reg_blk extends uvm_reg_block;

     `uvm_object_utils({{group.name|lower}}_grp_reg_blk)

  {% for group_entry in group.register_sets %}
  {%    if group_entry.repeat > 1 or group_entry.array %}
     {{group.name|lower}}_{{group_entry.set|lower}}_reg_blk {{group_entry.inst|lower}}[{{group_entry.repeat}}];
  {%    else %}
     {{group.name|lower}}_{{group_entry.set|lower}}_reg_blk {{group_entry.inst|lower}};
  {%    endif %}
  {% endfor %}

  {% for item in group_maps[group] %}
     uvm_reg_map {{item}}_map;
  {% endfor %}
  {% if used_maps|length > 1 %}
    {% for map in group_maps[group] %}
     bit disable_{{map}}_map = 1'b0;
    {% endfor %}
  {% endif %}

     function new(string name = "{{group.name|lower}}_grp_reg_blk");
        super.new(name, build_coverage(UVM_NO_COVERAGE));
     endfunction : new

     function void build();
  {% if group_maps[group]|length > 1 %}
    {% for item in group_maps[group] %}
        if (!disable_{{item}}_map) begin
           {{item}}_map = create_map("{{item}}_map", 0, {{project.get_address_width(item)}}, UVM_LITTLE_ENDIAN);
        end
    {% endfor %}
  {% else %}
    {% for item in group_maps[group] %}
        {{item}}_map = create_map("{{item}}_map", 0, {{project.get_address_width(item)}}, UVM_LITTLE_ENDIAN);
    {% endfor %}
  {% endif %}

  {% for group_entry in group.register_sets %}
    {% if group_entry.repeat > 1 or group_entry.array %}
        for (int i = 0; i < {{group_entry.repeat}}; i++) begin
           {% if use_new %}
           {{group_entry.inst|lower}}[i] = new($sformatf("{{group_entry.inst|lower}}[%0d]", i));
           {% else %}
           {{group_entry.inst|lower}}[i] = {{group.name|lower}}_{{group_entry.set|lower}}_reg_blk::type_id::create($sformatf("{{group_entry.inst|lower}}[%0d]", i));
           {% endif %}
      {% if group_entry.hdl: %}
           {{group_entry.inst|lower}}[i].configure(this, $sformatf("{{group_entry.hdl}}", i));
      {% else %}
           {{group_entry.inst|lower}}[i].configure(this, "");
      {% endif %}
      {% for item in group_maps[group] %}
        {% if group_maps[group]| length > 1 %}
           {{group_entry.inst|lower}}[i].disable_{{item}}_map = disable_{{item}}_map;
        {% endif %}
      {% endfor %}
           {{group_entry.inst|lower}}[i].build();
      {% for item in group_maps[group] %}
        {% if group_maps[group]| length > 1 %}
           if (!disable_{{item}}_map) begin
              {{item}}_map.add_submap({{group_entry.inst|lower}}[i].{{item}}_map, 'h{{"%x" | format(group_entry.offset)}} + (i * 'h{{"%x" | format(group_entry.repeat_offset)}}));
           end
        {% else %}
           {{item}}_map.add_submap({{group_entry.inst|lower}}[i].{{item}}_map, 'h{{"%x" | format(group_entry.offset)}} + (i * 'h{{"%x" | format(group_entry.repeat_offset)}}));
        {% endif %}
        {% if group_entry.no_uvm %}
           uvm_resource_db#(bit)::set({"REG::",{{group_entry.inst|lower}}[i].get_full_name(),".*"}, "NO_REG_TESTS", 1, this);
        {% endif %}
      {% endfor %}
        end
    {% else %}
        {% if use_new %}
        {{group_entry.inst|lower}} = new("{{group_entry.inst|lower}}");
        {% else %}
        {{group_entry.inst|lower}} = {{group.name|lower}}_{{group_entry.set|lower}}_reg_blk::type_id::create("{{group_entry.inst|lower}}");
        {% endif %}
        {{group_entry.inst|lower}}.configure(this, "{{group_entry.hdl}}");
      {% for item in group_maps[group] %}
        {% if group_maps[group]| length > 1 %}
        {{group_entry.inst|lower}}.disable_{{item}}_map = disable_{{item}}_map;
        {% endif %}
      {% endfor %}
        {{group_entry.inst|lower}}.build();
      {% for item in group_maps[group] %}
        {% if group_maps[group]| length > 1 %}
        if (!disable_{{item}}_map) {{item}}_map.add_submap({{group_entry.inst|lower}}.{{item}}_map, 'h{{"%x"| format(group_entry.offset)}});
        {% else %}
        {{item}}_map.add_submap({{group_entry.inst|lower}}.{{item}}_map, 'h{{"%x"| format(group_entry.offset)}});
        {% endif %}
        {% if group_entry.no_uvm %}
        uvm_resource_db#(bit)::set({"REG::",{{group_entry.inst|lower}}.get_full_name(),".*"}, "NO_REG_TESTS", 1, this);
        {% endif %}
      {% endfor %}
    {%  endif %}
  {% endfor %}
      endfunction: build
  endclass : {{group.name|lower}}_grp_reg_blk
{% endfor %}

  /* Top level register block */
  class {{project.short_name|lower}}_reg_block extends uvm_reg_block;

     `uvm_object_utils({{project.short_name|lower}}_reg_block)

{% for group in group_maps %}
{%   if group.repeat > 1 %}
     {{group.name|lower}}_grp_reg_blk {{group.name|lower}}[{{group.repeat}}];
{%   else %}
     {{group.name|lower}}_grp_reg_blk {{group.name|lower}};
{%   endif %}
{%- endfor %}
{% for data in used_maps %}
     uvm_reg_map {{data}}_map;
{% endfor %}
{% if used_maps|length > 1 %}
  {% for data in used_maps %}
     bit disable_{{data}}_map = 1'b0;
  {% endfor %}
{% endif %}

     function new(string name = "{{project.short_name|lower}}_reg_block");
        super.new(name, build_coverage(UVM_NO_COVERAGE));
     endfunction : new

     function void build();

{% for map in project.get_address_maps() %}
  {% if map.name in used_maps %}
    {% if used_maps|length > 1 %}
        if (!disable_{{map.name}}_map) {{map.name}}_map = create_map("{{map.name}}_map", 'h{{"%x" | format(map.base)}}, {{project.get_address_width(map.name)}}, UVM_LITTLE_ENDIAN);
    {% else %}
        {{map.name}}_map = create_map("{{map.name}}_map", 'h{{"%x" | format(map.base)}}, {{project.get_address_width(map.name)}}, UVM_LITTLE_ENDIAN);
    {% endif %}
  {% endif %}
{% endfor %}

{% for group in group_maps %}
  {% if group.repeat <= 1 %}
    {% if use_new %}
        {{group.name|lower}} = new("{{group.name|lower}}");
    {% else %}
        {{group.name|lower}} = {{group.name|lower}}_grp_reg_blk::type_id::create("{{group.name|lower}}");
    {% endif %}
        {{group.name|lower}}.configure(this, "{{group.hdl}}");
    {% if used_maps|length > 1 %}
      {% for set in used_maps %}
        {% if group.name in map2grp[set] %}
        {{group.name|lower}}.disable_{{set}}_map = disable_{{set}}_map;
        {% endif %}
      {% endfor %}
    {% endif %}
        {{group.name|lower}}.build();
	   
    {% if used_maps|length > 1 %}
      {%- for set in used_maps -%}
        {% if group.name in map2grp[set] %}
        if (!disable_{{set}}_map) {{set}}_map.add_submap({{group.name|lower}}.{{set}}_map, 'h{{"%x" | format(group.base)}});
        {% endif %}
      {% endfor %}
    {%- else -%}
      {% for set in used_maps %}
        {{set}}_map.add_submap({{group.name|lower}}.{{set}}_map, 'h{{"%x" | format(group.base)}});
      {% endfor %}

    {% endif %}
  {% else %}

        foreach ({{group.name|lower}}[i]) begin
    {% if use_new %}
           {{group.name|lower}}[i] = new($sformatf("{{group.name|lower}}[%0d]", i));
    {% else  %}
           {{group.name|lower}}[i] = {{group.name|lower}}_grp_reg_blk::type_id::create($sformatf("{{group.name|lower}}[%0d]", i));
    {% endif %}
           {{group.name|lower}}[i].configure(this, $sformatf("{{group.hdl}}", i));
    {% for mname in project.get_address_maps() %}
      {% if mname.name in used_maps %}
        {% if used_maps|length > 1 %}
           {{group.name|lower}}[i].disable_{{mname.name}}_map = disable_{{mname.name}}_map;
        {% endif %}
      {% endif %}
    {% endfor %}
           {{group.name|lower}}[i].build();
	   
    {% for mname in project.get_address_maps() %}
      {% if mname.name in used_maps %}
        {% if used_maps|length > 1 %}
           if (!disable_{{mname.name}}_map) {{mname.name}}_map.add_submap({{group.name|lower}}[i].{{mname.name}}_map, 'h{{"%x" | format(group.base)}} + (i * 'h{{"%x" | format(group.repeat_offset)}}));
        {% else %}
           {{mname.name}}_map.add_submap({{group.name|lower}}[i].{{mname.name}}_map, 'h{{"%x" | format(group.base)}} + (i * 'h{{"%x" | format(group.repeat_offset)}}));
        {% endif %}
      {% endif %}
    {% endfor %}
        end

  {% endif %}
{% endfor %}
        reset();
        lock_model();
     endfunction: build

  endclass : {{project.short_name|lower}}_reg_block

endpackage : {{project.short_name|lower}}_reg_pkg
