<script setup lang="ts">
import { reactive, ref, computed, onMounted, nextTick, watch, onBeforeUnmount } from 'vue'
import { ElInput, ElInputNumber, ElSelect, ElOption, ElTable, ElTableColumn, ElButton, ElMessage, ElMessageBox, ElUpload, UploadProps, ElIcon, ElImage } from 'element-plus'
import { addDishListApi, putDishListApi } from '@/api/vadmin/product/dish'
import { getBranchOptionsApi } from '@/api/vadmin/basicinfo/branch'
import { getDishCategoryOptionsApi } from '@/api/vadmin/product/dishcategory'
import { getDishStatusOptionsApi } from '@/api/vadmin/basicinfo/basicdict'
import { UploadFilled } from '@element-plus/icons-vue'
import { useAuthStore } from '@/store/modules/auth'
import { ButtonPre } from '@/components/ButtonPre'

const authStore = useAuthStore()

const token = computed(() => authStore.getToken)

defineOptions({
  name: 'ImportDish'
})

const IMPORT_STORAGE_KEY = 'IMPORT_DISH_PAYLOAD'
const IMPORT_DATA_CACHE_KEY = 'IMPORT_DISH_DATA_CACHE'

const createDefaultRow = () => ({
  id: undefined,
        name_unique: '',
        name_display: null,
        name_english: null,
        branch_id: 1,
        dish_category_id: 2,
        sale_price: null,
        order_number: null,
        sku_code: null,
        status: -1,
        dish_images: [],
  dish_images_display: [],
        action: null
})

const dataList = ref([createDefaultRow()])

const infoDefaults = {
  ready: '就绪.',
  success: '保存成功',
  error: '发生异常，请检查数据'
}

const infoMessage = reactive({
  mode: 'ready',
  text: infoDefaults.ready
})

const infoText = computed(() => infoMessage.text || infoDefaults[infoMessage.mode] || infoDefaults.ready)
const infoClass = computed(() => `info-${infoMessage.mode}`)

const setInfoMessage = (mode, text) => {
  const nextMode = ['ready', 'success', 'error'].includes(mode) ? mode : 'ready'
  infoMessage.mode = nextMode
  infoMessage.text = text || infoDefaults[nextMode]
}

const saveLoading = ref(false)
const editableColumns = computed(() => tableColumns.filter(col => col.enabled !== false))
const editableFields = computed(() => editableColumns.value.map(col => col.field))
const firstEditableField = computed(() => editableFields.value[0] || 'name_unique')

const applyPayload = (payload) => {
  if (Array.isArray(payload) && payload.length) {
    dataList.value = payload.map((item) => ({
      ...createDefaultRow(),
      ...item
    }))
    setInfoMessage('ready', `已载入 ${payload.length} 条菜品，等待维护`)
    // 保存到缓存
    nextTick(() => {
      saveDataToCache()
    })
  } else {
    dataList.value = [createDefaultRow()]
    setInfoMessage('ready', infoDefaults.ready)
    // 保存到缓存
    nextTick(() => {
      saveDataToCache()
    })
  }
}

// 序列化数据（排除 File 对象等不可序列化的内容）
const serializeDataList = (list) => {
  return list.map((row) => {
    const serialized = { ...row }
    // 处理图片数据：只保存 URL 字符串，不保存 File 对象
    if (Array.isArray(serialized.dish_images)) {
      serialized.dish_images = serialized.dish_images.map((item) => {
        if (Array.isArray(item)) {
          // 如果是 [previewUrl, 'add', fileName, file] 格式，只保存前三个元素
          return [item[0], item[1], item[2]]
        }
        return item
      })
    }
    return serialized
  })
}

// 保存数据到 sessionStorage
const saveDataToCache = () => {
  try {
    const serialized = serializeDataList(dataList.value)
    sessionStorage.setItem(IMPORT_DATA_CACHE_KEY, JSON.stringify(serialized))
  } catch (err) {
    console.error('保存数据缓存失败：', err)
  }
}

// 从 sessionStorage 恢复数据
const restoreDataFromCache = () => {
  try {
    const cache = sessionStorage.getItem(IMPORT_DATA_CACHE_KEY)
    if (!cache) return false
    const payload = JSON.parse(cache)
    if (Array.isArray(payload) && payload.length) {
      dataList.value = payload.map((item) => ({
        ...createDefaultRow(),
        ...item,
        // 恢复图片数组，确保格式正确
        dish_images: Array.isArray(item.dish_images) ? item.dish_images : [],
        dish_images_display: Array.isArray(item.dish_images_display) ? item.dish_images_display : []
      }))
      setInfoMessage('ready', `已恢复 ${payload.length} 条数据`)
      return true
    }
  } catch (err) {
    console.error('恢复数据缓存失败：', err)
  }
  return false
}

// 清除数据缓存
const clearDataCache = () => {
  try {
    sessionStorage.removeItem(IMPORT_DATA_CACHE_KEY)
  } catch (err) {
    console.error('清除数据缓存失败：', err)
  }
}

const hydrateFromStorage = () => {
  try {
    const cache = sessionStorage.getItem(IMPORT_STORAGE_KEY)
    if (cache) {
      const payload = JSON.parse(cache)
      applyPayload(payload)
      sessionStorage.removeItem(IMPORT_STORAGE_KEY)
      return
    }
    // 如果没有新传入的数据，尝试恢复缓存
    restoreDataFromCache()
  } catch (err) {
    console.error('导入批量维护缓存失败：', err)
    // 出错时也尝试恢复缓存
    restoreDataFromCache()
  }
}

const tableColumns = reactive([
  {
    field: 'id',
    label: 'ID',
    width: '50px',
    type: 'number',
    show: false,
    enabled: false
  },
  {
    field: 'name_unique',
    label: '名称',
    minwidth: '240px',
    type: 'text',
    show: true,
    enabled: true
  },
  {
    field: 'name_display',
    label: '显示名称',
    width: '240px',
    type: 'text',
    show: true,
    enabled: true
  },
  {
    field: 'name_english',
    label: '英文名称',
    width: '240px',
    type: 'text',
    show: true,
    enabled: true
  },
  {
    field: 'branch_id',
    label: '分店',
    width: '160px',
    type: 'select',
    show: true,
    enabled: true,
    options: []
  },
  {
    field: 'dish_category_id',
    label: '类别',
    width: '100px',
    type: 'select',
    show: true,
    enabled: true,
    options: []
  },
  {
    field: 'sku_code',
    label: 'SKU码',
    width: '120px',
    type: 'text',
    show: true,
    enabled: true
  },
  {
    field: 'sale_price',
    label: '基础售价',
    width: '80px',
    type: 'number',
    show: true,
    enabled: true
  },
  {
    field: 'dish_images',
    label: '图片',
    width: '320px',
    type: 'images',
    show: true,
    enabled: true
  },
  {
    field: 'order_number',
    label: '排序号',
    width: '60px',
    type: 'number',
    show: true,
    enabled: true
  },
  {
    field: 'status',
    label: '状态',
    width: '60px',
    type: 'select',
    show: true,
    enabled: false,
    options: []
  }
])

const visibleColumns = computed(() => tableColumns.filter(col => col.show !== false))

const loadOptions = async () => {
  const colBranch = tableColumns.find(col => col.field === 'branch_id')
  if (colBranch) {
    const res = await getBranchOptionsApi()
    colBranch.options = res.data
    console.log(res)
  }

  const colCategory = tableColumns.find(col => col.field === 'dish_category_id')
  if (colCategory) {
    const res = await getDishCategoryOptionsApi()
    colCategory.options = res.data
  }

  const colStatus = tableColumns.find(col => col.field === 'status')
  if (colStatus) {
    const res = await getDishStatusOptionsApi()
    colStatus.options = res.data
  }
}

// 当前正在编辑的单元格
const editingCell = ref('')

// 安全获取行数据
const getRowData = (scope) => {
  return scope?.row || {}
}

// 安全获取行索引
const getRowIndex = (scope) => {
  return scope?.$index ?? -1
}

// 检查是否为编辑状态
const isEditingCell = (scope, column) => {
  const index = getRowIndex(scope)
  return column.enabled && editingCell.value === `${index}-${column.field}`
}

// 处理单元格点击
const handleCellClick = (row, column) => {
  if (row && column?.property) {
    const colConfig = tableColumns.find(col => col.field === column.property)
    if (!colConfig || colConfig.enabled === false) return
    const index = dataList.value.indexOf(row)
    if (index !== -1) {
      editingCell.value = `${index}-${column.property}`
    }
  }
}

// 完成编辑
const handleEditComplete = (row, field) => {
  if (!row) return
  if (field) {
    const index = dataList.value.indexOf(row)
    if (index !== -1) {
      const cellKey = `${index}-${field}`
      if (editingCell.value === cellKey) {
        editingCell.value = ''
      }
      return
    }
  }
  editingCell.value = ''
}

// 删除行
const handleDelete = async (index) => {
  if (index >= 0 && index < dataList.value.length) {
    try {
      await ElMessageBox.confirm('确定要删除这一行吗？', '提示', {
        type: 'warning'
      })
      dataList.value.splice(index, 1)
      ElMessage.success('删除成功')
    } catch {
      // 用户取消删除
    }
  }
}

// 添加新行
const addRow = (showMessage = true) => {
  const newRow = createDefaultRow()
  dataList.value.push(newRow)
  const index = dataList.value.length - 1
  if (showMessage) {
    setInfoMessage('ready', '已新增 1 行，等待维护')
  }
  return index
}

const focusCell = (rowIndex, field) => {
  if (!field || rowIndex < 0 || rowIndex >= dataList.value.length) return
  editingCell.value = `${rowIndex}-${field}`
  // 使用 nextTick 确保 DOM 更新后再聚焦
  nextTick(() => {
    const cellKey = `${rowIndex}-${field}`
    // 查找对应的输入控件或容器
    const target = document.querySelector(`[data-cell-key="${cellKey}"]`)
    if (target) {
      // 如果是 images 列，直接聚焦容器
      if (target.classList.contains('image-container')) {
        target.focus()
      } else {
        // 其他列，查找内部的输入控件
        // 优先查找 input 元素
        let input = target.querySelector('input')
        if (!input) {
          // 查找 Element Plus 的输入框
          input = target.querySelector('.el-input__inner, .el-input__wrapper input')
        }
        if (!input && target.tagName === 'INPUT') {
          input = target
        }
        if (input) {
          input.focus()
          // 如果是文本输入框，选中所有文本
          if (input.type === 'text' && input.select && typeof input.select === 'function') {
            input.select()
          }
        } else {
          // 如果找不到输入框，尝试聚焦容器本身
          target.focus()
        }
      }
    }
  })
}

const handleAddRow = () => {
  const index = addRow()
  setTimeout(() => {
    focusCell(index, firstEditableField.value)
  }, 0)
}

// 格式化单元格显示值
const formatCellValue = (value, column) => {
  if (!value && value !== 0) return ''
  
  if (column.type === 'select' && column.options) {
    const option = column.options.find(opt => opt.value === value)
    return option ? option.label : value
  }
  return value
}

const ensureImageFields = (row) => {
  if (!row) return
  if (!Array.isArray(row.dish_images)) {
    row.dish_images = row.dish_images ? [...row.dish_images] : []
  }
  if (!Array.isArray(row.dish_images_display)) {
    if (Array.isArray(row.dish_images)) {
      row.dish_images_display = row.dish_images.map((item) => {
        if (Array.isArray(item)) return item[0]
        if (typeof item === 'string') return item.split('?')[0]
        return item
      })
    } else {
      row.dish_images_display = []
    }
  }
}

const getRowImages = (row) => {
  ensureImageFields(row)
  return row?.dish_images_display || []
}

const isActiveImage = (image) => typeof image === 'string' && image.length > 0 && !image.endsWith('?delete')

const getPreviewList = (row) => {
  return getRowImages(row).filter((image) => isActiveImage(image))
}

const getPreviewIndex = (row, image) => {
  const previewList = getPreviewList(row)
  return previewList.findIndex((item) => item === image)
}

const countActiveImages = (row) => {
  return getPreviewList(row).length
}

const canUploadMore = (row) => countActiveImages(row) < 10

const uploadFile = async (fileForm) => {
  try {
    const res = await fetch('/api/vadmin/system/upload/image/to/local', {
      method: 'POST',
      body: fileForm
    })
    if (!res.ok) {
      throw new Error(`HTTP错误：${res.status}`)
    }
    const data = await res.json()
    return {
      success: true,
      data
    }
  } catch (err) {
    const message = err instanceof Error ? err.message : '未知错误'
    return {
      success: false,
      message
    }
  }
}

const processRowImages = async (row) => {
  ensureImageFields(row)
  const dishImages = [...row.dish_images]
  const displayImages = [...row.dish_images_display]

  for (let index = 0; index < dishImages.length; index++) {
    const item = dishImages[index]
    if (Array.isArray(item)) {
      const fileLike = item[3]
      const rawFile = fileLike?.raw ?? fileLike
      if (!rawFile) {
        throw new Error('图片文件缺失，无法上传')
      }
      const fileForm = new FormData()
      fileForm.append('file', rawFile)
      fileForm.append('path', 'system')
      const res = await uploadFile(fileForm)
      if (!res.success || !res.data?.data?.remote_path) {
        throw new Error(res.message || '图片上传失败')
      }
      const remotePath = res.data.data.remote_path
      dishImages[index] = `${remotePath}?${item[1]}`
      displayImages[index] = `${remotePath}?${item[1]}`
    }
  }

  row.dish_images = dishImages
  row.dish_images_display = displayImages

  return {
    dish_images: [...dishImages],
    dish_images_display: [...displayImages]
  }
}

const buildRowPayload = async (row) => {
  const normalizedRow = {
    ...row,
    branch_id: Number(row.branch_id) || 1,
    dish_category_id: Number(row.dish_category_id) || 2,
    sale_price: row.sale_price ?? null,
    order_number: row.order_number ?? null,
    status: row.status ?? -1,
    sku_code: row.sku_code ?? null,
    action: null
  }

  const images = await processRowImages(normalizedRow)

  return {
    ...normalizedRow,
    dish_images: images.dish_images,
    dish_images_display: images.dish_images_display
  }
}

const requiredFields = ['name_unique', 'branch_id', 'dish_category_id']

const validateCellValue = (row, column) => {
  const value = row?.[column.field]
  if (requiredFields.includes(column.field)) {
    if (value === null || value === undefined || value === '') {
      return {
        valid: false,
        message: `${column.label || '该字段'}不能为空`
      }
    }
  }

  if (column.type === 'number') {
    if (value !== null && value !== undefined && value !== '' && Number.isNaN(Number(value))) {
      return {
        valid: false,
        message: `${column.label || '该字段'}必须是数字`
      }
    }
  }

  return { valid: true }
}

const moveToNextEditableCell = (rowIndex, field) => {
  const fields = editableFields.value
  if (!fields.length) return
  let colIndex = fields.indexOf(field)
  if (colIndex === -1) colIndex = 0
  let nextRow = rowIndex
  let nextCol = colIndex + 1
  if (nextCol >= fields.length) {
    nextCol = 0
    nextRow += 1
  }
  if (nextRow >= dataList.value.length) {
    nextRow = addRow(false)
  }
  focusCell(nextRow, fields[nextCol])
}

const moveToPreviousEditableCell = (rowIndex, field) => {
  const fields = editableFields.value
  if (!fields.length) return
  let colIndex = fields.indexOf(field)
  if (colIndex === -1) colIndex = 0
  let prevRow = rowIndex
  let prevCol = colIndex - 1
  if (prevCol < 0) {
    prevCol = fields.length - 1
    prevRow -= 1
  }
  if (prevRow < 0) {
    // 已经是第一行第一列，不跳转
    return
  }
  focusCell(prevRow, fields[prevCol])
}

// 跟踪 select 组件的下拉状态
const selectDropdownStates = ref(new Map())

const handleSelectKeyDown = (event, scope, column) => {
  // 只处理 Enter 和 Tab 键，不阻止方向键
  if (event.key === 'Enter' || event.key === 'Tab') {
    const cellKey = `${getRowIndex(scope)}-${column.field}`
    const isDropdownOpen = selectDropdownStates.value.get(cellKey) || false
    const isShiftTab = event.key === 'Tab' && event.shiftKey
    
    // 如果下拉框是打开的
    if (isDropdownOpen) {
      // Shift+Tab：关闭下拉框并反向跳转
      if (isShiftTab) {
        event.preventDefault()
        selectDropdownStates.value.set(cellKey, false)
        const row = getRowData(scope)
        const validation = validateCellValue(row, column)
        if (!validation.valid) {
          ElMessage.warning(validation.message)
          return
        }
        moveToPreviousEditableCell(getRowIndex(scope), column.field)
        return
      }
      
      // Tab 键（非 Shift）：关闭下拉框并正向跳转
      if (event.key === 'Tab' && !event.shiftKey) {
        event.preventDefault()
        // 关闭下拉框
        selectDropdownStates.value.set(cellKey, false)
        // 验证并跳转
        const row = getRowData(scope)
        const validation = validateCellValue(row, column)
        if (!validation.valid) {
          ElMessage.warning(validation.message)
          return
        }
        moveToNextEditableCell(getRowIndex(scope), column.field)
      }
      // Enter 键：让 Element Plus 默认处理（选择选项并关闭下拉框）
      // 不阻止，让 change 事件处理
      return
    }
    
    // 如果下拉框未打开，Enter 或 Tab 都跳转
    event.preventDefault()
    const row = getRowData(scope)
    const validation = validateCellValue(row, column)
    if (!validation.valid) {
      ElMessage.warning(validation.message)
      return
    }
    
    if (isShiftTab) {
      moveToPreviousEditableCell(getRowIndex(scope), column.field)
    } else {
      moveToNextEditableCell(getRowIndex(scope), column.field)
    }
  }
  // 方向键等按键不处理，让 Element Plus 默认处理
}

const handleSelectVisibleChange = (visible, scope, column) => {
  const cellKey = `${getRowIndex(scope)}-${column.field}`
  selectDropdownStates.value.set(cellKey, visible)
}

const handleEditingKeyDown = (event, scope, column) => {
  if (event.key !== 'Enter' && event.key !== 'Tab') return
  
  // 检测 Shift+Tab 组合键（反向跳转）
  const isShiftTab = event.key === 'Tab' && event.shiftKey
  
  event.preventDefault()
  const row = getRowData(scope)
  const validation = validateCellValue(row, column)
  if (!validation.valid) {
    ElMessage.warning(validation.message)
    return
  }
  
  if (isShiftTab) {
    moveToPreviousEditableCell(getRowIndex(scope), column.field)
  } else {
    moveToNextEditableCell(getRowIndex(scope), column.field)
  }
}

const beforeImageUpload: UploadProps['beforeUpload'] = (rawFile) => {
  const isImage = ['image/jpeg', 'image/gif', 'image/png'].includes(rawFile.type)
  const isLtSize = rawFile.size / 1024 / 1024 < 2
  if (!isImage) {
    ElMessage.error('上传图片必须是 JPG/GIF/PNG/ 格式!')
  }
  if (!isLtSize) {
    ElMessage.error('上传图片大小不能超过2MB!')
  }
  return isImage && isLtSize
}

const handleFileChange = (row, file) => {
  if (!row || !file?.raw) return
  ensureImageFields(row)
  const exists = row.dish_images.some((item) => Array.isArray(item) && item[2] === file.name)
  if (exists) return
  const previewUrl = URL.createObjectURL(file.raw)
  row.dish_images_display.push(previewUrl)
  row.dish_images.push([previewUrl, 'add', file.name, file])
}

const handleRemoveImage = (row, index) => {
  if (!row || typeof index !== 'number') return
  ensureImageFields(row)
  if (Array.isArray(row.dish_images[index])) {
    row.dish_images_display.splice(index, 1)
    row.dish_images.splice(index, 1)
  } else {
    const display = row.dish_images_display[index]
    const stored = row.dish_images[index]
    if (typeof display === 'string') {
      row.dish_images_display[index] = `${display.split('?')[0]}?delete`
    }
    if (typeof stored === 'string') {
      row.dish_images[index] = `${stored.split('?')[0]}?delete`
    }
  }
}

const dragState = reactive({
  row: null,
  dragIndex: -1,
  dragOverIndex: -1
})

const handleDragStart = (row, index, event) => {
  if (!event?.dataTransfer) return
  dragState.row = row
  dragState.dragIndex = index
  dragState.dragOverIndex = -1
  event.dataTransfer.effectAllowed = 'move'
  event.dataTransfer.setData('text/plain', index.toString())
  setTimeout(() => {
    event.target?.classList?.add('dragging')
  }, 0)
}

const handleDragOver = (event) => {
  event.preventDefault()
  if (event.dataTransfer) {
    event.dataTransfer.dropEffect = 'move'
  }
}

const handleDragEnter = (row, index, event) => {
  event.preventDefault()
  if (dragState.row === row) {
    dragState.dragOverIndex = index
  }
}

const handleDragLeave = (row, event) => {
  if (dragState.row !== row) return
  const currentTarget = event.currentTarget
  if (currentTarget && !currentTarget.contains(event.relatedTarget)) {
    dragState.dragOverIndex = -1
  }
}

const handleDrop = (row, targetIndex, event) => {
  event.preventDefault()
  if (dragState.row !== row || !event.dataTransfer) return
  const sourceIndex = parseInt(event.dataTransfer.getData('text/plain'), 10)
  if (Number.isNaN(sourceIndex) || sourceIndex === targetIndex) {
    resetDragState()
    return
  }

  ensureImageFields(row)
  if (sourceIndex >= 0 && targetIndex >= 0) {
    const displayImages = [...row.dish_images_display]
    const [movedDisplay] = displayImages.splice(sourceIndex, 1)
    displayImages.splice(targetIndex, 0, movedDisplay)
    row.dish_images_display = displayImages

    const storedImages = [...row.dish_images]
    const [movedStored] = storedImages.splice(sourceIndex, 1)
    storedImages.splice(targetIndex, 0, movedStored)
    row.dish_images = storedImages
  }

  resetDragState()
}

const handleDragEnd = () => {
  resetDragState()
  const draggingElements = document.querySelectorAll('.dragging')
  draggingElements.forEach((el) => el.classList.remove('dragging'))
}

const resetDragState = () => {
  dragState.row = null
  dragState.dragIndex = -1
  dragState.dragOverIndex = -1
}

const isDraggingImage = (row, index) => dragState.row === row && dragState.dragIndex === index
const isDragOverImage = (row, index) => dragState.row === row && dragState.dragOverIndex === index

const handleSave = async () => {
  if (!dataList.value.length) {
    setInfoMessage('ready', '暂无可保存的数据')
    ElMessage.warning('请先添加菜品数据')
    return
  }
  saveLoading.value = true
  try {
    for (const row of dataList.value) {
      const payload = await buildRowPayload(row)
      if (payload.id) {
        console.log("save", payload)
        await putDishListApi(payload)
      } else {
        await addDishListApi(payload)
      }
    }
    setInfoMessage('success', `成功保存 ${dataList.value.length} 条菜品记录`)
    ElMessage.success('保存成功')
    // 保存成功后清除缓存
    clearDataCache()
  } catch (err) {
    const message = err instanceof Error ? err.message : '保存失败，请稍后重试'
    setInfoMessage('error', message)
    ElMessage.error(message)
  } finally {
  saveLoading.value = false
  }
}

const handleReturn = () => {
  setInfoMessage('ready', '已暂停批量维护')
}

// 监听 dataList 变化，自动保存到缓存（使用防抖，避免频繁保存）
let saveTimer = null
watch(
  () => dataList.value,
  () => {
    if (saveTimer) {
      clearTimeout(saveTimer)
    }
    saveTimer = setTimeout(() => {
      saveDataToCache()
    }, 500) // 500ms 防抖
  },
  { deep: true }
)

onMounted(() => {
  hydrateFromStorage()
  loadOptions()
})

onBeforeUnmount(() => {
  // 组件卸载前保存数据
  if (saveTimer) {
    clearTimeout(saveTimer)
  }
  saveDataToCache()
})
</script>

<template>
  <div class="add-row-section">
    <div class="toolbar-left">
    <ButtonPre stype="new" @click="handleAddRow()" />
    </div>
    <div class="toolbar-info" :class="infoClass">
      {{ infoText }}
    </div>
    <div class="toolbar-actions">
      <ButtonPre stype="save" :loading="saveLoading" @click="handleSave()" />
      <ButtonPre stype="return" @click="handleReturn()" />
    </div>
  </div>
  <div class="editable-table-container">
    <el-table
      :data="dataList"
      border
      style="width: 100%"
      @cell-click="handleCellClick"
    >
      <el-table-column
        v-for="column in visibleColumns"
        :key="column.field"
        :prop="column.field"
        :label="column.label"
        :width="column.width || 'auto'"
        :minwidth="column.minwidth"
      >
        <template #default="scope">
          <template v-if="column.type === 'images'">
            <div 
              class="image-container"
              :data-cell-key="`${getRowIndex(scope)}-${column.field}`"
              :tabindex="isEditingCell(scope, column) ? 0 : -1"
              @keydown.enter.prevent="handleEditingKeyDown($event, scope, column)"
              @keydown.tab.prevent="handleEditingKeyDown($event, scope, column)"
              @click="handleCellClick(getRowData(scope), { property: column.field })"
            >
              <template
                v-for="(image, index) in getRowImages(getRowData(scope))"
                :key="`${index}-${image}`"
              >
                <div
                  v-if="isActiveImage(image)"
                  class="image-group"
                  :class="{
                    dragging: isEditingCell(scope, column) && isDraggingImage(getRowData(scope), index),
                    'drag-over': isEditingCell(scope, column) && isDragOverImage(getRowData(scope), index)
                  }"
                  :draggable="isEditingCell(scope, column)"
                  @click.stop
                  @dragstart="isEditingCell(scope, column) ? (e) => handleDragStart(getRowData(scope), index, e) : undefined"
                  @dragover.prevent="isEditingCell(scope, column) ? handleDragOver : undefined"
                  @dragenter.prevent="isEditingCell(scope, column) ? (e) => handleDragEnter(getRowData(scope), index, e) : undefined"
                  @dragleave="isEditingCell(scope, column) ? (e) => handleDragLeave(getRowData(scope), e) : undefined"
                  @drop.prevent="isEditingCell(scope, column) ? (e) => handleDrop(getRowData(scope), index, e) : undefined"
                  @dragend="isEditingCell(scope, column) ? handleDragEnd : undefined"
                >
                  <el-image
                    :src="image"
                    class="image-item"
                    fit="cover"
                    :preview-src-list="getPreviewList(getRowData(scope))"
                    :initial-index="getPreviewIndex(getRowData(scope), image)"
                    preview-teleported
                  />
                  <div 
                    v-if="isEditingCell(scope, column)"
                    class="remove-btn" 
                    @click.stop="handleRemoveImage(getRowData(scope), index)"
                  >
                    x
                  </div>
                </div>
              </template>
              <div 
                v-if="isEditingCell(scope, column) && canUploadMore(getRowData(scope))" 
                class="image-group-uploader"
              >
                <el-upload
                  action="/api/vadmin/system/upload/image/to/local"
                  :data="{ path: 'system' }"
                  :show-file-list="false"
                  multiple
                  :auto-upload="false"
                  :before-upload="beforeImageUpload"
                  @change="(file) => handleFileChange(getRowData(scope), file)"
                  accept="image/jpeg,image/gif,image/png"
                  name="file"
                  drag
                  :headers="{ Authorization: token }"
                  :limit="10"
                >
                  <div>
                    <ElIcon class="el-icon--upload"><UploadFilled /></ElIcon>
                    <div class="upload-text">拖拽或点击上传</div>
                  </div>
                </el-upload>
              </div>
            </div>
          </template>
          <template v-else-if="isEditingCell(scope, column)">
            <el-input-number 
              v-if="column.type === 'number'"
              :data-cell-key="`${getRowIndex(scope)}-${column.field}`"
              v-model="getRowData(scope)[column.field]"
              :controls="false"
              size="small"
              @keydown.enter.prevent="handleEditingKeyDown($event, scope, column)"
              @keydown.tab.prevent="handleEditingKeyDown($event, scope, column)"
              @blur="handleEditComplete(getRowData(scope), column.field)"
            />
            <el-select
              v-else-if="column.type === 'select'"
              :data-cell-key="`${getRowIndex(scope)}-${column.field}`"
              v-model="getRowData(scope)[column.field]"
              size="small"
              @keydown.enter="handleSelectKeyDown($event, scope, column)"
              @keydown.tab="handleSelectKeyDown($event, scope, column)"
              @visible-change="(visible) => handleSelectVisibleChange(visible, scope, column)"
              @change="handleEditComplete(getRowData(scope), column.field)"
            >
              <el-option 
                v-for="option in column.options"
                :key="option.value"
                :label="option.label"
                :value="option.value"
              />
            </el-select>
            <el-input 
              v-else-if="column.type === 'text'"
              :data-cell-key="`${getRowIndex(scope)}-${column.field}`"
              v-model="getRowData(scope)[column.field]"
              size="small"
              @keydown.enter.prevent="handleEditingKeyDown($event, scope, column)"
              @keydown.tab.prevent="handleEditingKeyDown($event, scope, column)"
              @blur="handleEditComplete(getRowData(scope), column.field)"
            />
          </template>
          <template v-else>
            {{ formatCellValue(getRowData(scope)[column.field], column) }}
          </template>
        </template>
      </el-table-column>
      <el-table-column label="操作" width="80px">
        <template #default="scope">
          <el-button
            type="danger"
            link
            size="small"
            @click="handleDelete(getRowIndex(scope))"
          >
            删除
          </el-button>
        </template>
      </el-table-column>
    </el-table>
  </div>
</template>

<style lang="less" scoped>
.editable-table-container {
  margin: 10px 10px 0px 10px;
}

.add-row-section {
  display: flex;
  align-items: center;
  margin: 10px 10px 0px 10px;
}

.toolbar-left {
  flex: 0 0 auto;
}

.toolbar-info {
  flex: 1;
  margin: 0 10px;
  background: #fff;
  border: none;
  min-height: 32px;
  display: flex;
  align-items: center;
  padding: 0 10px;
  font-size: 13px;
  color: #666;
  font-style: italic;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.toolbar-info.info-success {
  color: #0f5132;
  border-color: #0f5132;
}

.toolbar-info.info-error {
  color: #d93025;
  border-color: #d93025;
}

.toolbar-actions {
  flex: 0 0 auto;
  margin-left: auto;
  display: flex;
  gap: 10px;
}

:deep(.el-table .cell) {
  padding: 4px 8px;
}

:deep(.el-input-number) {
  width: 100%;
}

:deep(.el-select) {
  width: 100%;
}

.image-container {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
  padding: 0;
}

.image-container {
  .image-group {
    position: relative;
    width: 60px;
    height: 60px;
    margin: 0;
  }

  .image-item {
    width: 100%;
    height: 100%;
    border-radius: 4px;
    object-fit: cover;
    border: 1px solid #dcdfe6;
    transition: all 0.3s ease;
  }

  .image-item:hover {
    transform: scale(1.05);
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
  }

  .remove-btn {
    position: absolute;
    top: -4px;
    right: -4px;
    width: 16px;
    height: 16px;
    background: #f56c6c;
    color: white;
    border-radius: 50%;
    display: flex;
    align-items: center;
    justify-content: center;
    cursor: pointer;
    font-size: 10px;
    font-weight: bold;
    opacity: 0;
    transition: opacity 0.3s ease;
  }

  .image-group:hover .remove-btn {
    opacity: 1;
  }

  .image-group.dragging {
    opacity: 0.5;
    border-color: #409eff;
    transform: scale(0.95);
    box-shadow: 0 6px 18px rgba(0, 0, 0, 0.2);
    cursor: grabbing;
    z-index: 1000;
  }

  .image-group.drag-over {
    transform: scale(1.15);
    border: 2px solid #3b82f6;
    box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.2);
    transform: scale(1.05);
    z-index: 10;
    transition: all 0.2s ease;
  }

  .image-group-uploader {
    width: 112px;
    height: 56px;
    flex-shrink: 0;

    :deep(.el-upload) {
    border: 2px dashed #c0c4cc;
    width: 100% !important;
      height: 100% !important;
    margin: 0 !important;
    border-radius: 6px;
      padding: 0 !important;
      line-height: 1;
      display: flex;
      align-items: center;
      justify-content: center;
  }

    :deep(.el-upload:hover) {
    border-color: #409eff;
    background: #f0f7ff;
    color: #409eff;
  }

    :deep(.el-upload-dragger) {
    width: 100% !important;
      height: 56px !important;
      min-height: 56px !important;
      border: none !important;
    display: flex;
      flex-direction: column;
    align-items: center;
    justify-content: center;
      padding: 4px 6px !important;
      box-sizing: border-box;
      overflow: hidden;
    }

    :deep(.el-icon--upload) {
      width: 36px;
      height: 36px;
      margin-top: -6px;
    }

    :deep(.upload-text) {
    font-size: 12px;
      margin-top: -16px;
    text-align: center;
      line-height: 1.1;
      white-space: normal;
      width: 100%;
      word-break: break-all;
    }
  }
}
</style>
