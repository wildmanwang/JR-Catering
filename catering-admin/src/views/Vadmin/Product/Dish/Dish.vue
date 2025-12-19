<script setup lang="tsx">
  import { ref } from 'vue'
  import { BaseGrid } from '@/wintemplate/baseGrid'
  import { getDishListApi, delDishListApi, getDishStatusOptionsApi, addDishListApi, putDishListApi } from '@/api/vadmin/product/dish'
  import { getKitchenListApi } from '@/api/vadmin/product/kitchen'
  import { ContentWrap } from '@/components/ContentWrap'
  import { formSchema, rules, tabs } from './components/Response.vue'
  
  defineOptions({
    name: 'Dish'
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
      field: 'dish_images',
      label: '图片',
      type: 'image' as const,
      width: '80px',
      imageSize: 'small' as const
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
      field: 'kitchen_id',
      label: '厨部id',
      type: 'text' as const,
      show: false
    },
    {
      field: 'kitchen_name_unique',
      label: '厨部',
      type: 'text' as const,
      width: '160px'
    },
    {
      field: 'spec',
      label: '规格',
      type: 'text' as const,
      width: '200px'
    },
    {
      field: 'price',
      label: '基础售价',
      type: 'text' as const,
      width: '120px'
    },
    {
      field: 'order_number',
      label: '排序号',
      type: 'text' as const,
      width: '80px'
    },
    {
      field: 'time_on',
      label: '首次上架日期',
      type: 'text' as const,
      width: '140px'
    },
    {
      field: 'time_off',
      label: '下架日期',
      type: 'text' as const,
      width: '140px'
    },
    {
      field: 'status',
      label: '状态',
      type: 'status' as const,
      width: '100px',
      optionsApi: getDishStatusOptionsApi,
      optionsIdField: 'value',
      optionsLabelFormat: [['field', 'label']]
    },
    {
      field: 'action',
      label: '操作',
      type: 'action' as const,
      align: 'center' as const,
      fixed: 'right' as const,
      // 如果不配置 actionOptions，BaseGrid 会自动使用集成的操作函数
      // actionOptions: [] // 可以留空，使用默认操作
    }
  ]
  
  // ==================== 数据接口 ====================
  // 注意：错误处理和返回格式转换已转移到 BaseGrid.vue 中，这里只需传递 API 函数
  const fetchDataApi = getDishListApi
  
  // ==================== 查询条件配置 ====================
  const searchConditions = [
    {
      field: 'status',
      label: '状态',
      type: 'select' as const,
      // 不配置 options，BaseGrid 会自动从 status 列的 optionsApi 获取数据
      units: 1 // 1单位 = 160px
    },
    {
      field: 'fuzzy_query_str',
      label: '模糊查询',
      type: 'input' as const,
      placeholder: '请输入名称或显示名称',
      units: 3 // 默认3单位（480px）
    },
    {
      field: 'price',
      label: '价格',
      type: 'number' as const,
      placeholder: '请输入价格',
      units: 1 // 1单位 = 160px
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
      label: '菜品'
      // 如果不提供 onClick，BaseGrid 会自动使用集成的 openImport
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
        :fetch-del-api="delDishListApi"
        :search-conditions="searchConditions"
        :toolbar-buttons="toolbarButtons"
        :quick-query-list="{
          title: '按厨部查询',
          dataApi: () => getKitchenListApi({ is_active: true }),
          field: 'kitchen_id',
          idField: 'id',
          labelFormat: [['field', 'name_unique']],
          showAllOption: true,
          allOptionLabel: '（全部）'
        }"
        node-key="id"
        :show-action="true"
        :page-title="'菜品'"
        :form-schema="formSchema"
        :rules="rules"
        :tabs="tabs"
        :add-api="addDishListApi"
        :edit-api="putDishListApi"
        :import-route="'/product/dish/import'"
        :import-storage-key="'IMPORT_DISH_PAYLOAD'"
        :import-label="'菜品'"
      />
    </ContentWrap>
  </template>
  