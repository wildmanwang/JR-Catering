<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { ImportGrid, type ImportGridColumn } from '@/wintemplate/importGrid'
import { addDishListApi } from '@/api/vadmin/product/dish'
import { getDishStatusOptionsApi } from '@/api/vadmin/product/dish'
import { getKitchenListApi } from '@/api/vadmin/product/kitchen'
import { ElMessage } from 'element-plus'

defineOptions({
  name: 'DishImport'
})

// ==================== Props 定义 ====================
interface Props {
  /** 从父窗口传入的记录列表 */
  initialData?: any[]
}

const props = withDefaults(defineProps<Props>(), {
  initialData: () => []
})

// ==================== Emits 定义 ====================
const emit = defineEmits<{
  cancel: []
  success: []
}>()

// ==================== 状态管理 ====================
const importGridRef = ref<InstanceType<typeof ImportGrid>>()

/** 菜品状态选项 */
const dishStatusOptions = ref<Array<{ id: number; name: string }>>([])

/** 厨部选项 */
const kitchenOptions = ref<Array<{ id: number; name_unique: string }>>([])

// ==================== 创建默认行 ====================
const createDefaultRow = () => ({
  id: undefined,
  name_unique: '',
  name_display: undefined,
  name_english: undefined,
  kitchen_id: undefined,
  sale_price: undefined,
  order_number: undefined,
  sku_code: undefined,
  status: 0,
  dish_images: [],
  dish_images_display: []
})

// ==================== 列配置 ====================
const columns = computed<ImportGridColumn[]>(() => [
  {
    field: 'id',
    label: 'ID',
    type: 'text',
    width: '50px',
    show: false,
    editable: false
  },
  {
    field: 'name_unique',
    label: '名称',
    type: 'text',
    minWidth: '240px',
    editable: true
  },
  {
    field: 'name_display',
    label: '显示名称',
    type: 'text',
    width: '240px',
    editable: true
  },
  {
    field: 'name_english',
    label: '英文名称',
    type: 'text',
    width: '240px',
    editable: true
  },
  {
    field: 'kitchen_id',
    label: '厨部',
    type: 'select',
    width: '160px',
    editable: true,
    options: () => kitchenOptions.value.map(item => ({
      label: item.name_unique,
      value: item.id
    }))
  },
  {
    field: 'sale_price',
    label: '基础售价',
    type: 'number',
    width: '120px',
    editable: true
  },
  {
    field: 'order_number',
    label: '排序号',
    type: 'number',
    width: '100px',
    editable: true
  },
  {
    field: 'sku_code',
    label: 'SKU编码',
    type: 'text',
    width: '150px',
    editable: true
  },
  {
    field: 'description',
    label: '简介',
    type: 'textarea',
    width: '200px',
    editable: true
  },
  {
    field: 'status',
    label: '状态',
    type: 'select',
    width: '100px',
    editable: false,
    options: () => dishStatusOptions.value.map((item: { id: number; name: string }) => ({
      label: item.name,
      value: item.id
    }))
  },
  {
    field: 'dish_images',
    label: '图片',
    type: 'image',
    width: '320px',
    editable: true,
    imageField: 'dish_images',
    imageDisplayField: 'dish_images_display'
  }
])

// ==================== 数据获取 ====================
/**
 * 获取菜品状态选项
 */
const getDishStatusOptions = async () => {
  try {
    const res = await getDishStatusOptionsApi()
    if (res?.data) {
      dishStatusOptions.value = res.data
    }
  } catch (err) {
    console.error('获取菜品状态列表失败：', err)
    dishStatusOptions.value = []
  }
}

/**
 * 获取厨部列表
 */
const getKitchenOptions = async () => {
  try {
    const res = await getKitchenListApi({ is_active: true })
    if (res?.data) {
      kitchenOptions.value = res.data
    }
  } catch (err) {
    console.error('获取厨部列表失败：', err)
    kitchenOptions.value = []
  }
}

// ==================== 保存处理 ====================
/**
 * 批量保存接口
 */
const handleSave = async (data: any[]) => {
  try {
    // 过滤掉空行（所有字段都为空的行）
    const validData = data.filter(row => {
      return row.name_unique || row.name_display || row.kitchen_id
    })
    
    if (validData.length === 0) {
      ElMessage.warning('没有有效数据需要保存')
      return
    }
    
    // 批量保存
    for (const row of validData) {
      // 移除 id（新增记录）
      const { id, ...rowData } = row
      
      // 处理图片字段：移除 display 字段，只保留 dish_images
      const { dish_images_display, ...submitData } = rowData
      
      await addDishListApi(submitData)
    }
    
    ElMessage.success(`成功保存 ${validData.length} 条记录`)
    emit('success')
  } catch (error) {
    const errorMessage = error instanceof Error ? error.message : '保存失败'
    ElMessage.error(errorMessage)
    throw error
  }
}

/**
 * 处理取消
 */
const handleCancel = () => {
  emit('cancel')
}

/**
 * 处理保存成功
 */
const handleSuccess = () => {
  emit('success')
}

// ==================== 生命周期 ====================
onMounted(async () => {
  await getDishStatusOptions()
  await getKitchenOptions()
})
</script>

<template>
  <div class="dish-import-wrapper">
    <ImportGrid
      ref="importGridRef"
      :columns="columns"
      :initial-data="props.initialData"
      :create-default-row="createDefaultRow"
      :save-api="handleSave"
      @cancel="handleCancel"
      @success="handleSuccess"
    />
  </div>
</template>

<style scoped lang="less">
.dish-import-wrapper {
  width: 100%;
  height: 100%;
  display: flex;
  flex-direction: column;
}
</style>

