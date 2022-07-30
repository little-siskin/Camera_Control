var $;
layui.config({
	base : "js/"
}).use(['form','layer','jquery','table'],function(){
	var form = layui.form,
	table1=layui.table,
	layer = parent.layer === undefined ? layui.layer : parent.layer,
	$ = layui.jquery;
	table1.render({
	elem: '#demo1',//渲染对象
	height: 'full-88',//表格高度
	url: 'detailuser', //数据接口
	where: {key: ''},//给后台传的参数
	id: 'testReload',
	cols: [[ //表头
	      {field: 'id', title: '用户号', sort: true, fixed: 'left'}
	      ,{field: 'user_name', title: '用户名', align: 'center'}
	      ,{field: 'pwd', title: '登陆密码', align:'center'}
		  ,{field:'email',title:'邮箱',align:'center'}
		  ,{field:'authority',title:'权限',align:'center'}
		  ,{field:'cam_id',title:'摄像头id',align:'center'}
	      ,{fixed: 'right',  align:'center', toolbar: '#barDemo'} //这里的toolbar值是模板元素的选择器
	    ]]
	  });
	
	
})
