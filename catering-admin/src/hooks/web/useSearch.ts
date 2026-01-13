import { ref, unref, nextTick } from 'vue'
import { FormSchema, FormSetProps } from '@/components/Form'
import { SearchExpose, SearchProps } from '@/components/Search'

export const useSearch = () => {
  // Search实例
  const searchRef = ref<SearchExpose>()

  /**
   * @param ref Search实例
   * @param elRef ElForm实例
   */
  const register = (ref: SearchExpose) => {
    searchRef.value = ref
  }

  const getSearch = async () => {
    await nextTick()
    const search = unref(searchRef)
    if (!search) {
      console.error('The Search is not registered. Please use the register method to register')
    }
    return search
  }

  // 一些内置的方法
  const methods = {
    /**
     * @description 设置search组件的props
     * @param field FormItem的field
     */
    setProps: async (props: SearchProps = {}) => {
      const search = await getSearch()
      search?.setProps(props)
      if (props.model) {
        search?.setValues(props.model)
      }
    },

    /**
     * @description 设置form的值
     * @param data 需要设置的数据
     */
    setValues: async (data: Recordable) => {
      const search = await getSearch()
      search?.setValues(data)
    },

    /**
     * @description 设置schema
     * @param schemaProps 需要设置的schemaProps
     */
    setSchema: async (schemaProps: FormSetProps[]) => {
      const search = await getSearch()
      search?.setSchema(schemaProps)
    },

    /**
     * @description 新增schema
     * @param formSchema 需要新增数据
     * @param index 在哪里新增
     */
    addSchema: async (formSchema: FormSchema, index?: number) => {
      const search = await getSearch()
      search?.addSchema(formSchema, index)
    },

    /**
     * @description 删除schema
     * @param field 删除哪个数据
     */
    delSchema: async (field: string) => {
      const search = await getSearch()
      search?.delSchema(field)
    },

    /**
     * @description 获取表单数据
     * @returns form data
     */
    getFormData: async <T = Recordable>(): Promise<T> => {
      const search = await getSearch()
      if (!search) {
        return {} as T
      }
      // 使用 Search 组件暴露的 getFormData 方法，它会从 Form 组件获取实际的 formModel
      // 因为 Form 组件内部的 formModel 会随着用户输入而更新
      if (search.getFormData && typeof search.getFormData === 'function') {
        try {
          const formData = await search.getFormData(false) as T
          return formData
        } catch (error) {
          console.error('useSearch: Failed to get form data from Search.getFormData:', error)
        }
      }
      // 如果 Search 组件没有 getFormData 方法，尝试从 Form 组件获取
      try {
        const formExpose = await search.getElFormExpose()
        if (formExpose && formExpose.formModel) {
          return JSON.parse(JSON.stringify(formExpose.formModel)) as T
        }
      } catch (error) {
        console.error('useSearch: Failed to get form data from Form component:', error)
      }
      // 如果都失败，返回 Search 组件的 formModel（向后兼容）
      return search?.formModel as T
    }
  }

  return {
    searchRegister: register,
    searchMethods: methods
  }
}
