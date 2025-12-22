<script setup lang="tsx">
import { ref } from 'vue'
import { BaseGrid } from '@/wintemplate/baseGrid'
import {
  getDishGroupListApi,
  delDishGroupApi,
  addDishGroupApi,
  putDishGroupApi
} from '@/api/vadmin/product/dishGroup'
import { getDishGroupTypeListApi } from '@/api/vadmin/product/dishGroupType'
import { ContentWrap } from '@/components/ContentWrap'
import { formSchema, rules, tabs } from './components/Response.vue'

defineOptions({
  name: 'DishGroup'
})

// ==================== 状态管理 ====================
const gridRef = ref<InstanceType<typeof BaseGrid>>()

// ==================== 列定义 ====================
const columns = [
  {
    field: 'selection',
    label: '',
    type: 'selection' as const
  },
  {
    field: 'id',
    label: 'ID',
    type: 'text' as const,
    show: false
  },
  {
    field: 'name_unique',
    label: '名称',
    type: 'text' as const,
    minWidth: '240px',
    showConfig: false
  },
  {
    field: 'name_display',
    label: '显示名称',
    type: 'text' as const,
    minWidth: '240px',
    show: true,
    showConfig: true // 可配置显示/隐藏
  },
  {
    field: 'dish_group_type_id',
    label: '厨部id',
    type: 'text' as const,
    show: false
  },
  {
    field: 'stype',
    label: '类型',
    type: 'select' as const,
    width: '100px'
  },
  {
    field: 'order_number',
    label: '排序号',
    type: 'text' as const,
    width: '80px'
  },
  {
    field: 'is_active',
    label: '是否启用',
    type: 'select' as const,
    width: '100px',
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
  },
  {
    field: 'action',
    label: '操作',
    type: 'action' as const,
    align: 'center' as const,
    fixed: 'right' as const
    // 如果不配置 actionOptions，BaseGrid 会自动使用集成的操作函数
    // actionOptions: [] // 可以留空，使用默认操作
  }
]

// ==================== 数据接口 ====================
// 注意：错误处理和返回格式转换已转移到 BaseGrid.vue 中，这里只需传递 API 函数
const fetchDataApi = getDishGroupListApi

// ==================== 查询条件配置 ====================
const searchConditions = [
  {
    field: 'is_active',
    label: '是否启用',
    type: 'select' as const,
    units: 1, // 1单位 = 160px
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
  {
    field: 'fuzzy_query_str',
    label: '模糊查询',
    type: 'input' as const,
    placeholder: '请输入名称或显示名称',
    units: 3 // 默认3单位（480px）
  }
]

  // ==================== Toolbar 按钮配置 ====================
  const toolbarButtons = [
    {
      stype: 'new' as const
      // 如果不提供 onClick，BaseGrid 会自动使用集成的 addAction
    } as const,
    {
      stype: 'import' as const,
      label: '菜品分组',
      importRoute: '/product/dishGroup/importBase'
      // 如果不提供 onClick，BaseGrid 会自动使用集成的 openImport
      // importStorageKey 会根据 windowId 自动生成，无需配置
      // importLabel 会自动使用按钮的 label，无需单独配置
    },
    {
      stype: 'batch' as const,
      label: '删除'
      // 如果不提供 onClick，BaseGrid 会自动使用集成的 delData
    }
  ]

// ==================== 生命周期 ====================
// 注意：选项数据的获取已转移到 BaseGrid.vue 中，通过列定义的 optionsApi 自动获取
</script>

<template>
  <ContentWrap>
    <BaseGrid
      ref="gridRef"
      :columns="columns"
      :fetch-data-api="fetchDataApi"
      :fetch-del-api="delDishGroupApi"
      :search-conditions="searchConditions"
      :toolbar-buttons="toolbarButtons"
      :quick-query-list="{
        title: '按菜品组类型',
        dataApi: () => getDishGroupTypeListApi({ is_active: true }),
        field: 'dish_group_type_id',
        idField: 'id',
        labelFormat: [['field', 'name_unique']],
        showAllOption: true,
        allOptionLabel: '（全部）'
      }"
      node-key="id"
      :show-action="true"
      :page-title="'菜品分组'"
      :window-id="'DishGroup'"
      :form-schema="formSchema"
      :rules="rules"
      :tabs="tabs"
      :add-api="addDishGroupApi"
      :edit-api="putDishGroupApi"
    />
  </ContentWrap>
</template>
