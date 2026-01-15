/**
 * 菜品分组批量导入/维护页面
 * 
 * 使用 ImportGrid 组件实现 Excel 风格的批量编辑
 * 数据通过 sessionStorage 从父窗口（Dish.vue）传递
 */
<script setup lang="ts">
import { computed, ref } from 'vue'
import { useRouter } from 'vue-router'
import { ContentWrap } from '@/components/ContentWrap'
import { ImportGrid, type ImportGridColumn, type SaveConfig, type ToolbarButton } from '@/wintemplate/ImportGrid'
import { addDishGroupApi, putDishGroupApi, getDishGroupApi } from '@/api/vadmin/product/dishGroup'
import { getDishGroupTypeListApi } from '@/api/vadmin/product/dishGroupType'
import { getBranchListApi } from '@/api/vadmin/system/branch'
import { getDishGroupStypeOptionsApi } from '@/api/vadmin/product/dishGroup'

defineOptions({
  name: 'DishGroupImport'
})

const router = useRouter()
const importGridRef = ref<InstanceType<typeof ImportGrid>>()

// ==================== 常量 ====================
// 注意：storageKey 必须与 BaseGrid 生成的 key 一致
// BaseGrid 生成的格式：IMPORT_${windowId}_PAYLOAD
const IMPORT_STORAGE_KEY = 'IMPORT_DishGroup_PAYLOAD'

// ==================== 列配置 ====================
const columns = computed<ImportGridColumn[]>(() => [
  {
    field: 'id',
    label: 'ID',
    width: '80px',
    type: 'text',
    show: false
  },
  {
    field: 'name_unique',
    label: '名称',
    minWidth: '200px',
    type: 'text',
    show: true,
    required: true,
    value: ''
  },
  {
    field: 'name_display',
    label: '显示名称',
    minWidth: '200px',
    type: 'text',
    show: true,
    required: true
  },
  {
    field: 'name_english',
    label: '英文名称',
    minWidth: '200px',
    type: 'text',
    show: true
  },
  {
    field: 'dish_group_type_id',
    label: '菜品组类型',
    width: '100px',
    type: 'select',
    show: true,
    required: true,
    optionsApi: () => getDishGroupTypeListApi({ is_active: true }),
    optionsIdField: 'id',
    optionsLabelFormat: [['field', 'name_unique']],
    selectProps: {
      disabled: false,
      filterable: false
    }
  },
  {
    field: 'stype',
    label: '类型',
    width: '160px',
    type: 'select',
    optionsApi: () => getDishGroupStypeOptionsApi(),
    optionsIdField: 'value',
    optionsLabelFormat: [['field', 'label']],
    show: true
  },
  {
    field: 'branch_id',
    label: '门店',
    width: '160px',
    type: 'select',
    optionsApi: () => getBranchListApi({ is_active: true }),
    optionsIdField: 'id',
    optionsLabelFormat: [['field', 'name_unique']],
    show: true
  },
  {
    field: 'order_number',
    label: '排序号',
    width: '80px',
    type: 'number',
    show: true
  },
  {
    field: 'is_active',
    label: '是否启用',
    width: '60px',
    type: 'select',
    show: true,
    options: [
      {
        label: '是',
        value: true
      },
      {
        label: '否',
        value: false
      }
    ],
    value: true
  }
])

// ==================== 配置 ====================
const toolbarButtons = computed<ToolbarButton[]>(() => [
  { type: 'add', stype: 'new' },
  { type: 'save', stype: 'save' },
  { 
    type: 'custom', 
    stype: 'setting', 
    label: '菜品', 
    alignRight: true,
    onClick: () => {
      // 打开 ImportDetail 前，先获取 ImportGrid 的当前实际数据并保存到 sessionStorage
      // 确保传递的是当前页面的实际数据，而不是缓存数据
      if (importGridRef.value) {
        const currentData = importGridRef.value.getData()
        if (currentData && currentData.length > 0) {
          try {
            const payload = {
              action: 'import',
              data: currentData
            }
            sessionStorage.setItem(IMPORT_STORAGE_KEY, JSON.stringify(payload))
          } catch {
            // 保存数据到 sessionStorage 失败，静默处理
          }
        }
      }
      router.push('/product/dishGroup/importDetail')
    }
  }
])

const saveConfig = computed<SaveConfig>(() => ({
  requiredFields: [
    { field: 'name_unique', label: '名称' },
    { field: 'name_display', label: '显示名称' },
    { field: 'dish_group_type_id', label: '菜品组类型' }
  ],
  addApi: addDishGroupApi,
  updateApi: putDishGroupApi,
  getDetailApi: getDishGroupApi,
  preprocessData: (data: any, isNew: boolean) => {
    return isNew ? { ...data, is_active: true } : data
  }
}))

</script>

<template>
  <ContentWrap>
    <ImportGrid
      ref="importGridRef"
      :columns="columns"
      :storage-key="IMPORT_STORAGE_KEY"
      :save-config="saveConfig"
      :toolbar-buttons="toolbarButtons"
    />
  </ContentWrap>
</template>

