<script setup lang="tsx">
  import { ref, computed, onMounted } from 'vue'
  import { ElDrawer } from 'element-plus'
  import { BaseGrid } from '@/wintemplate/baseGrid'
  import { BaseFree } from '@/wintemplate/baseFree'
  import { getDishListApi, delDishListApi, getDishStatusOptionsApi, addDishListApi, putDishListApi } from '@/api/vadmin/product/dish'
  import { getKitchenListApi } from '@/api/vadmin/product/kitchen'
  import { ContentWrap } from '@/components/ContentWrap'
  import { formSchema, rules, tabs } from './components/Response.vue'
  import DishImport from './components/Import.vue'
  
  defineOptions({
    name: 'Dish'
  })
  
  // ==================== 状态管理 ====================
  const dishStatusOptions = ref<Array<{ label: string; value: number }>>([])
  const kitchenOptions = ref<Array<{ id: number; name_unique: string }>>([])
  const gridRef = ref<InstanceType<typeof BaseGrid>>()
  
  // 弹窗相关状态
  const dialogVisible = ref(false)
  const dialogMode = ref<'add' | 'edit' | 'view'>('add')
  const currentRow = ref<any>(null)
  const saveLoading = ref(false)
  const pageTitle = '菜品' // 主窗口标题
  
  // 导入窗口相关状态
  const importDrawerVisible = ref(false)
  const importInitialData = ref<any[]>([])
  
  // 字段选项数据映射（传递给 BaseFree，避免重复请求）
  const fieldOptions = computed(() => ({
    status: () => dishStatusOptions.value,
    kitchen_id: () => kitchenOptions.value
  }))
  
  // ==================== 数据获取 ====================
  /**
   * 获取菜品状态选项
   */
  const getOptions = async () => {
    try {
      const res = await getDishStatusOptionsApi()
      if (!res?.data) {
        console.warn('返回菜品状态列表为空')
        dishStatusOptions.value = []
        return
      }
      dishStatusOptions.value = res.data
    } catch (err) {
      console.error('获取菜品状态列表失败：', err)
      dishStatusOptions.value = []
    }
  }
  
  /**
   * 获取厨部列表（用于左侧快捷查询和表单下拉框）
   */
  const fetchKitchens = async () => {
    try {
      const res = await getKitchenListApi({ is_active: true })
      if (!res?.data) {
        kitchenOptions.value = []
        return []
      }
      // 保存到 kitchenOptions，供表单使用
      kitchenOptions.value = res.data
      // 返回格式：{ id, name_unique, ... }（用于快捷查询）
      return res.data.map((kitchen: any) => ({
        id: kitchen.id,
        label: kitchen.name_unique
      }))
    } catch (err) {
      console.error('获取厨部列表失败：', err)
      kitchenOptions.value = []
      return []
    }
  }
  
  // ==================== 列定义 ====================
  const columns = [
    {
      field: 'selection',
      label: '',
      type: 'selection' as const
    },
    {
      field: 'dish_image',
      label: '图片',
      type: 'image' as const,
      width: '110px',
      imageListField: 'dish_images',
      imageHeight: '60px'
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
      width: '160px'
    },
    {
      field: 'unit',
      label: '单位',
      type: 'text' as const,
      width: '160px'
    },
    {
      field: 'price',
      label: '基础售价',
      type: 'text' as const,
      width: '120px'
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
      statusOptions: () => dishStatusOptions.value
    },
    {
      field: 'action',
      label: '操作',
      type: 'action' as const,
      width: '180px',
      align: 'center' as const,
      fixed: 'right' as const,
      actionOptions: [
        {
          type: 'edit',
          onClick: (row: any) => editAction(row)
        },
        {
          type: 'other',
          label: '查看',
          onClick: (row: any) => viewAction(row)
        },
        {
          type: 'delete',
          onClick: (row: any) => delData(row)
        }
      ]
    }
  ]
  
  // ==================== 数据接口 ====================
  /**
   * 数据获取接口
   */
  const fetchDataApi = async (params: {
    page: number
    limit: number
    [key: string]: any
  }) => {
    try {
      const res = await getDishListApi(params)
      // 处理数据（参考 Dish.vue 的数据处理逻辑）
      if (res.data) {
        res.data.map((row: any) => row.dish_images.sort((a: string, b: string) => a.localeCompare(b)))
        res.data.forEach(
          (o: any) => (o.dish_images = o.dish_images.map((p: string) => p.split('-').slice(1).join('-')))
        )
      }
      return {
        data: res.data || [],
        count: res.count || 0
      }
    } catch (err: any) {
      console.error('获取菜品列表失败：', err.message)
      return {
        data: [],
        count: 0
      }
    }
  }
  
  /**
   * 删除接口
   */
  const fetchDelApi = async (ids: string[] | number[] | number | string) => {
    const res = await delDishListApi(ids)
    return res.code === 200
  }
  
  // ==================== 操作函数 ====================
  /**
   * 新增操作
   */
  const addAction = () => {
    dialogMode.value = 'add'
    currentRow.value = null
    dialogVisible.value = true
  }
  
  /**
   * 编辑操作
   */
  const editAction = (row: any) => {
    dialogMode.value = 'edit'
    // 复制行数据，避免直接修改原数据
    currentRow.value = { ...row }
    dialogVisible.value = true
  }
  
  /**
   * 查看操作
   */
  const viewAction = (row: any) => {
    dialogMode.value = 'view'
    currentRow.value = { ...row }
    dialogVisible.value = true
  }
  
  /**
   * 删除操作
   */
  const delData = async (row?: any) => {
    if (!gridRef.value) return
  
    if (row) {
      // 删除单行
      await gridRef.value.tableMethods.delList(true, [row.id])
    } else {
      // 批量删除
      await gridRef.value.tableMethods.delList(true)
    }
    // delList 方法会自动刷新列表并显示消息
  }
  
  /**
   * 提交接口（新增或修改）
   * @param data - 表单数据
   * @param mode - 操作模式（'add' | 'edit'），如果提供则优先使用，否则使用 dialogMode
   */
  const submitApi = async (data: any, mode?: 'add' | 'edit') => {
    // 优先使用传入的 mode 参数（支持继续新增/拷贝新增时的模式切换）
    // 如果没有传入 mode，则使用 dialogMode（向后兼容）
    const operationMode = mode || dialogMode.value
    if (operationMode === 'add') {
      return await addDishListApi(data)
    } else {
      return await putDishListApi(data)
    }
  }
  
  /**
   * 保存成功回调
   */
  const handleSuccess = () => {
    // 刷新列表
    if (gridRef.value) {
      gridRef.value.getList()
    }
  }
  
  /**
   * 取消操作
   */
  const handleCancel = () => {
    dialogVisible.value = false
    currentRow.value = null
  }
  
  // ==================== 查询条件配置 ====================
  const searchConditions = [
    {
      field: 'status',
      label: '状态',
      type: 'select' as const,
      options: () => dishStatusOptions.value,
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
  
  // ==================== 导入操作 ====================
  /**
   * 打开导入窗口
   * @param data - 从父窗口传入的记录列表（可以为空）
   */
  const openImport = (data: any[] = []) => {
    importInitialData.value = data
    importDrawerVisible.value = true
  }
  
  /**
   * 关闭导入窗口
   */
  const closeImport = () => {
    importDrawerVisible.value = false
    importInitialData.value = []
  }
  
  /**
   * 导入成功回调
   */
  const handleImportSuccess = () => {
    closeImport()
    // 刷新列表
    if (gridRef.value) {
      gridRef.value.getList()
    }
  }
  
  // ==================== Toolbar 按钮配置 ====================
  const toolbarButtons = [
    {
      stype: 'new' as const,
      onClick: addAction
    },
    {
      stype: 'import' as const,
      label: '导入',
      onClick: () => openImport()
    },
    {
      stype: 'batch' as const,
      label: '删除',
      onClick: () => delData()
    }
  ]
  
  // ==================== 生命周期 ====================
  onMounted(async () => {
    await getOptions()
    await fetchKitchens() // 初始化厨部选项数据
  })
  </script>
  
  <template>
    <ContentWrap>
      <BaseGrid
        ref="gridRef"
        :columns="columns"
        :fetch-data-api="fetchDataApi"
        :fetch-del-api="fetchDelApi"
        :search-conditions="searchConditions"
        :toolbar-buttons="toolbarButtons"
        :quick-query-list="{
          title: '按厨部查询',
          data: fetchKitchens,
          field: 'kitchen_id',
          showAllOption: true,
          allOptionLabel: '（全部）'
        }"
        node-key="id"
        :show-action="true"
      />
    </ContentWrap>
  
    <!-- 弹窗 -->
    <BaseFree
      v-model="dialogVisible"
      :page-title="pageTitle"
      :mode="dialogMode"
      :save-loading="saveLoading"
      :form-schema="formSchema"
      :rules="rules"
      :current-row="currentRow"
      :submit-api="submitApi"
      :tabs="tabs"
      :field-options="fieldOptions"
      @success="handleSuccess"
      @cancel="handleCancel"
    />
    
    <!-- 导入窗口 -->
    <ElDrawer
      v-model="importDrawerVisible"
      title="表格导入"
      :size="'100%'"
      :close-on-click-modal="false"
      destroy-on-close
    >
      <DishImport
        :initial-data="importInitialData"
        @cancel="closeImport"
        @success="handleImportSuccess"
      />
    </ElDrawer>
  </template>
  