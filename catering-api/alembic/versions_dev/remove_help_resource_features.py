"""remove help/resource menus and tables

Revision ID: remove_help_resource_features
Revises: move_log_menus
Create Date: 2025-11-25 18:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy import text

# revision identifiers, used by Alembic.
revision = 'remove_help_resource_features'
down_revision = 'move_log_menus'
branch_labels = None
depends_on = None


def upgrade():
    connection = op.get_bind()

    # 删除地图配置相关的系统设置
    map_tab = connection.execute(
        text("SELECT id FROM vadmin_system_settings_tab WHERE tab_name = :tab_name AND is_delete = 0"),
        {"tab_name": "map_distribution"}
    ).fetchone()
    if map_tab:
        tab_id = map_tab[0]
        op.execute(text("DELETE FROM vadmin_system_settings WHERE tab_id = :tab_id").bindparams(tab_id=tab_id))
        op.execute(text("DELETE FROM vadmin_system_settings_tab WHERE id = :tab_id").bindparams(tab_id=tab_id))

    # 删除指定菜单
    titles = [
        "用户分布",
        "空气质量",
        "智慧大屏",
        "图片资源",
        "资源管理",
        "常见问题表单",
        "常见问题",
        "常见问题类别",
        "帮助中心",
    ]
    for title in titles:
        op.execute(text("DELETE FROM vadmin_auth_menu WHERE title = :title").bindparams(title=title))

    # 删除帮助中心与资源管理相关数据表
    op.execute(text("DROP TABLE IF EXISTS vadmin_help_issue"))
    op.execute(text("DROP TABLE IF EXISTS vadmin_help_issue_category"))
    op.execute(text("DROP TABLE IF EXISTS vadmin_resource_images"))


def downgrade():
    connection = op.get_bind()

    # 重新创建帮助中心与资源管理相关表
    op.create_table(
        'vadmin_help_issue_category',
        sa.Column('name', sa.String(length=50), nullable=False, comment='类别名称'),
        sa.Column('platform', sa.String(length=8), nullable=False, comment='展示平台'),
        sa.Column('is_active', sa.Boolean(), nullable=False, comment='是否可见'),
        sa.Column('create_user_id', sa.Integer(), nullable=False, comment='创建人'),
        sa.Column('id', sa.Integer(), nullable=False, primary_key=True, comment='主键ID'),
        sa.Column('create_datetime', sa.DateTime(), server_default=sa.text('now()'), nullable=False, comment='创建时间'),
        sa.Column('update_datetime', sa.DateTime(), server_default=sa.text('now()'), nullable=False, comment='更新时间'),
        sa.Column('delete_datetime', sa.DateTime(), nullable=True, comment='删除时间'),
        sa.Column('is_delete', sa.Boolean(), nullable=False, comment='是否软删除'),
        sa.ForeignKeyConstraint(['create_user_id'], ['vadmin_auth_user.id'], ondelete='RESTRICT'),
        comment='常见问题类别表'
    )
    op.create_index('ix_vadmin_help_issue_category_name', 'vadmin_help_issue_category', ['name'])
    op.create_index('ix_vadmin_help_issue_category_platform', 'vadmin_help_issue_category', ['platform'])

    op.create_table(
        'vadmin_resource_images',
        sa.Column('filename', sa.String(length=255), nullable=False, comment='原图片名称'),
        sa.Column('image_url', sa.String(length=500), nullable=False, comment='图片链接'),
        sa.Column('create_user_id', sa.Integer(), nullable=False, comment='创建人'),
        sa.Column('id', sa.Integer(), nullable=False, primary_key=True, comment='主键ID'),
        sa.Column('create_datetime', sa.DateTime(), server_default=sa.text('now()'), nullable=False, comment='创建时间'),
        sa.Column('update_datetime', sa.DateTime(), server_default=sa.text('now()'), nullable=False, comment='更新时间'),
        sa.Column('delete_datetime', sa.DateTime(), nullable=True, comment='删除时间'),
        sa.Column('is_delete', sa.Boolean(), nullable=False, comment='是否软删除'),
        sa.ForeignKeyConstraint(['create_user_id'], ['vadmin_auth_user.id'], ondelete='RESTRICT'),
        comment='图片素材表'
    )

    op.create_table(
        'vadmin_help_issue',
        sa.Column('category_id', sa.Integer(), nullable=False, comment='类别'),
        sa.Column('title', sa.String(length=255), nullable=False, comment='标题'),
        sa.Column('content', sa.Text(), nullable=False, comment='内容'),
        sa.Column('view_number', sa.Integer(), nullable=False, comment='查看次数'),
        sa.Column('is_active', sa.Boolean(), nullable=False, comment='是否可见'),
        sa.Column('create_user_id', sa.Integer(), nullable=False, comment='创建人'),
        sa.Column('id', sa.Integer(), nullable=False, primary_key=True, comment='主键ID'),
        sa.Column('create_datetime', sa.DateTime(), server_default=sa.text('now()'), nullable=False, comment='创建时间'),
        sa.Column('update_datetime', sa.DateTime(), server_default=sa.text('now()'), nullable=False, comment='更新时间'),
        sa.Column('delete_datetime', sa.DateTime(), nullable=True, comment='删除时间'),
        sa.Column('is_delete', sa.Boolean(), nullable=False, comment='是否软删除'),
        sa.ForeignKeyConstraint(['category_id'], ['vadmin_help_issue_category.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['create_user_id'], ['vadmin_auth_user.id'], ondelete='RESTRICT'),
        comment='常见问题记录表'
    )
    op.create_index('ix_vadmin_help_issue_title', 'vadmin_help_issue', ['title'])

    # 还原地图配置 tab 及配置项
    op.execute(text("""
        INSERT INTO vadmin_system_settings_tab (title, classify, tab_label, tab_name, hidden, disabled, create_datetime, update_datetime, is_delete)
        VALUES ('地图配置', 'map', '用户分布', 'map_distribution', 1, 0, NOW(), NOW(), 0)
    """))
    map_tab = connection.execute(
        text("SELECT id FROM vadmin_system_settings_tab WHERE tab_name = :tab_name AND is_delete = 0"),
        {"tab_name": "map_distribution"}
    ).fetchone()
    if map_tab:
        tab_id = map_tab[0]
        settings = [
            ("开发者Key", "map_key", None, "申请好的Web端开发者Key，首次调用 load 时必填"),
            ("中心点位置", "map_center", "[105.602725, 37.076636]", "初始化地图中心点位置"),
            ("显示样式", "map_style", "amap://styles/normal", "设置地图的显示样式"),
            ("地图级别", "map_zoom", "5", "初始化地图级别"),
            ("地图模式", "map_view_mode", "3D", "是否为3D地图模式"),
            ("俯仰角度", "map_pitch", "20", "地图初始俯仰角度，有效范围 0 度- 83 度"),
        ]
        for label, key, value, remark in settings:
            op.execute(text("""
                INSERT INTO vadmin_system_settings (config_label, config_key, config_value, remark, disabled, tab_id, create_datetime, update_datetime, is_delete)
                VALUES (:label, :key, :value, :remark, 0, :tab_id, NOW(), NOW(), 0)
            """).bindparams(label=label, key=key, value=value, remark=remark, tab_id=tab_id))

    # 还原菜单
    def insert_menu(data):
        op.execute(text("""
            INSERT INTO vadmin_auth_menu (title, icon, redirect, component, path, disabled, hidden, `order`, menu_type, parent_id, perms, noCache, breadcrumb, affix, noTagsView, canTo, alwaysShow, create_datetime, update_datetime, is_delete)
            VALUES (:title, :icon, :redirect, :component, :path, :disabled, :hidden, :order, :menu_type, :parent_id, :perms, :noCache, :breadcrumb, :affix, :noTagsView, :canTo, :alwaysShow, NOW(), NOW(), 0)
        """).bindparams(**data))
        return connection.execute(
            text("SELECT id FROM vadmin_auth_menu WHERE title = :title AND is_delete = 0 ORDER BY id DESC LIMIT 1"),
            {"title": data["title"]}
        ).fetchone()[0]

    dashboard = connection.execute(
        text("SELECT id FROM vadmin_auth_menu WHERE title = '仪表盘' AND is_delete = 0")
    ).fetchone()
    if dashboard:
        insert_menu({
            "title": "用户分布",
            "icon": None,
            "redirect": None,
            "component": "views/Dashboard/Map",
            "path": "map",
            "disabled": 0,
            "hidden": 0,
            "order": 2,
            "menu_type": "1",
            "parent_id": dashboard[0],
            "perms": None,
            "noCache": 0,
            "breadcrumb": 1,
            "affix": 0,
            "noTagsView": 0,
            "canTo": 0,
            "alwaysShow": 0,
        })

    screen_menu_id = insert_menu({
        "title": "智慧大屏",
        "icon": "icon-park-solid:data-sheet",
        "redirect": "/screen/air",
        "component": None,
        "path": "/screen",
        "disabled": 0,
        "hidden": 0,
        "order": 3,
        "menu_type": "0",
        "parent_id": None,
        "perms": None,
        "noCache": 0,
        "breadcrumb": 1,
        "affix": 0,
        "noTagsView": 0,
        "canTo": 0,
        "alwaysShow": 1,
    })
    insert_menu({
        "title": "空气质量",
        "icon": None,
        "redirect": None,
        "component": "views/Vadmin/Screen/Air/Air",
        "path": "air",
        "disabled": 0,
        "hidden": 0,
        "order": 0,
        "menu_type": "1",
        "parent_id": screen_menu_id,
        "perms": None,
        "noCache": 0,
        "breadcrumb": 1,
        "affix": 0,
        "noTagsView": 0,
        "canTo": 0,
        "alwaysShow": 0,
    })

    resource_menu_id = insert_menu({
        "title": "资源管理",
        "icon": "line-md:image",
        "redirect": None,
        "component": "#",
        "path": "/resource",
        "disabled": 0,
        "hidden": 0,
        "order": 4,
        "menu_type": "0",
        "parent_id": None,
        "perms": None,
        "noCache": 0,
        "breadcrumb": 1,
        "affix": 0,
        "noTagsView": 0,
        "canTo": 0,
        "alwaysShow": 1,
    })
    insert_menu({
        "title": "图片资源",
        "icon": None,
        "redirect": None,
        "component": "views/Vadmin/Resource/Image/Image",
        "path": "images",
        "disabled": 0,
        "hidden": 0,
        "order": 1,
        "menu_type": "1",
        "parent_id": resource_menu_id,
        "perms": None,
        "noCache": 0,
        "breadcrumb": 1,
        "affix": 0,
        "noTagsView": 0,
        "canTo": 0,
        "alwaysShow": 0,
    })

    help_menu_id = insert_menu({
        "title": "帮助中心",
        "icon": "material-symbols:help-rounded",
        "redirect": None,
        "component": "#",
        "path": "/help",
        "disabled": 0,
        "hidden": 0,
        "order": 100,
        "menu_type": "0",
        "parent_id": None,
        "perms": None,
        "noCache": 0,
        "breadcrumb": 1,
        "affix": 0,
        "noTagsView": 0,
        "canTo": 0,
        "alwaysShow": 1,
    })

    insert_menu({
        "title": "常见问题类别",
        "icon": None,
        "redirect": None,
        "component": "views/Vadmin/Help/IssueCategory/IssueCategory",
        "path": "issue/category",
        "disabled": 0,
        "hidden": 0,
        "order": 0,
        "menu_type": "1",
        "parent_id": help_menu_id,
        "perms": None,
        "noCache": 0,
        "breadcrumb": 1,
        "affix": 0,
        "noTagsView": 0,
        "canTo": 0,
        "alwaysShow": 0,
    })
    insert_menu({
        "title": "常见问题",
        "icon": None,
        "redirect": None,
        "component": "views/Vadmin/Help/Issue/Issue",
        "path": "issue",
        "disabled": 0,
        "hidden": 0,
        "order": 1,
        "menu_type": "1",
        "parent_id": help_menu_id,
        "perms": None,
        "noCache": 0,
        "breadcrumb": 1,
        "affix": 0,
        "noTagsView": 0,
        "canTo": 0,
        "alwaysShow": 0,
    })
    insert_menu({
        "title": "常见问题表单",
        "icon": None,
        "redirect": None,
        "component": "views/Vadmin/Help/Issue/components/Write",
        "path": "issue/form",
        "disabled": 0,
        "hidden": 1,
        "order": 99,
        "menu_type": "1",
        "parent_id": help_menu_id,
        "perms": None,
        "noCache": 0,
        "breadcrumb": 1,
        "affix": 0,
        "noTagsView": 0,
        "canTo": 0,
        "alwaysShow": 0,
    })

