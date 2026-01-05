<script lang="ts">
  import { reactive } from 'vue'
  import { useValidator } from '@/hooks/web/useValidator'
  import type { FreeFormField } from '@/wintemplate/baseFree'
  import { getDishGroupStypeOptionsApi } from '@/api/vadmin/product/dishGroup'
  import { getDishGroupTypeListApi } from '@/api/vadmin/product/dishGroupType'
  import { getBranchListApi } from '@/api/vadmin/system/branch'
  
  const { required } = useValidator()
  
  // ==================== 表单字段配置 ====================
  export const formSchema: FreeFormField[] = [
    {
      field: 'name_unique',
      label: '名称',
      colProps: {
        span: 24
      },
      component: 'Input',
      newCopy: true
    },
    {
      field: 'name_display',
      label: '显示名称',
      colProps: {
        span: 24
      },
      component: 'Input',
      newCopy: true
    },
    {
      field: 'name_english',
      label: '英文名称',
      colProps: {
        span: 24
      },
      component: 'Input',
      newCopy: true
    },
    {
      field: 'dish_group_type_id',
      label: '菜品组类型',
      colProps: {
        span: 12
      },
      component: 'Select',
      componentProps: {
        multiple: false,
        props: {
          label: 'name_unique',
          value: 'id'
        }
      },
      newCopy: true,
      optionsApi: () => getDishGroupTypeListApi({ is_active: true }),
      optionsIdField: 'id',
      optionsLabelFormat: [['field', 'name_unique']]
    },
    {
      field: 'stype',
      label: '类型',
      colProps: {
        span: 12
      },
      component: 'Select',
      optionsApi: () => getDishGroupStypeOptionsApi(),
      optionsIdField: 'value',
      optionsLabelFormat: [['field', 'label']]
    },
    {
      field: 'branch_id',
      label: '门店',
      colProps: {
        span: 12
      },
      component: 'Select',
      newCopy: false,
      optionsApi: () => getBranchListApi({ is_active: true }),
      optionsIdField: 'id',
      optionsLabelFormat: [['field', 'name_unique']]
    },
    {
      field: 'order_number',
      label: '排序号',
      colProps: {
        span: 12
      },
      component: 'Input',
      newCopy: true
    },
    {
      field: 'is_active',
      label: '是否启用',
      colProps: {
        span: 12
      },
      component: 'Select',
      componentProps: {
        options: [
          {
            label: '是',
            value: true
          },
          {
            label: '否',
            value: false
          }
        ]
      },
      value: true
    }
  ]
  
  // ==================== 表单验证规则 ====================
  export const rules = reactive({
    name_unique: [required()],
    dish_group_type_id: [required()]
  })
</script>

<template>
  <div style="display: none;"></div>
</template>

<style lang="less" scoped>
</style>

