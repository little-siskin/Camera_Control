layui.config({//框架的固定，配置的使用
	base : "js/"
}).use(['form','layer','jquery','laypage','table'],function(){//组件，使用组件完成功能：from:表单；
	var form = layui.form,
		layer = parent.layer === undefined ? layui.layer : parent.layer,
		laypage = layui.laypage,
		table = layui.table,
		$ = layui.$;//以上只是将所需要的文件拿出来，以便于后面使用。

//==================一个table实例================================//table怎么设置
	  table.render({
	    elem: '#demo',//渲染对象
	    height: '274px',//表格高度
	    url: 'queryUsers1/', //数据接口
	    where: {id: ''},//给后台传的参数
	    page: true, //开启分页
		limits: [5,10], //每页条数选项
	    limit: 5,//每页显示信息条数
	    id: 'testReload',
	    cols: [[ //表头
	      {field: 'id', title: 'ID', sort: true, fixed: 'left'}
	      ,{field: 'user_name', title: '用户名', align: 'center'}
		  ,{field: 'email', title: '邮箱', align: 'center'}
	      ,{field: 'pwd', title: '登陆密码', align:'center'}
		  ,{field:'authority',title:'权限',align:'center'}
		  ,{field:'cam_id',title:'摄像头ID',align:'center'}
	      ,{fixed: 'right',  align:'center', toolbar: '#barDemo'} //这里的toolbar值是模板元素的选择器
	    ]]
	  });
	  
	  table.render({
	    elem: '#demo1',//渲染对象
	    height: '250px',//表格高度
	    url: 'queryUsers2/', //数据接口
	    where: {id: ''},//给后台传的参数
	    page: true, //开启分页
		limits: [4], //每页条数选项
	    limit: 4,//每页显示信息条数
	    id: 'testReload1',
	    cols: [[ //表头
	      {field: 'id', title: '摄像头ID', sort: true, fixed: 'left'}
	      ,{field: 'cam_ip', title: '摄像头IP', align: 'center'}
		  ,{field: 'rtsp_ip', title: '摄像头rstp ip', align: 'center'}
	      ,{fixed: 'right',  align:'center', toolbar: '#barDemo_1'} //这里的toolbar值是模板元素的选择器
	    ]]
	  });
//====================点击【搜索】按钮事件===========================
  var active = {
		  reload : function() {
			  var demoReload = $('#demoReload');
							// 执行重载
			  table.reload('testReload', {//reload重新加载
				page : {
					  curr : 1// 重新从第 1 页开始
					  },
					  where : {//要查询的字段
						id:  demoReload.val()
						}
					  });
			  }
  };
  /**
   * 点击操作后刷新数据
   */
  var active_op = {
		  reload : function() {
			  var demoReload = $('#demoReload');
							// 执行重载
			  table.reload('testReload', {//reload重新加载
					  where : {//要查询的字段
						id:  demoReload.val()
						}
					  });
			  }
  };
// 绑定搜索事件
  //将事件绑定在按钮上
  $('#btn .layui-btn').on('click', function() {
	  var type = $(this).data('type');
	  active[type] ? active[type].call(this) : '';
	  });
  
//=============绑定【添加】事件============================
	$(window).one("resize",function(){//基于框架做的
		$(".add_btn").click(function(){
			var index = layui.layer.open({
				title : "【添加用户信息】",
				icon: 2,
				type : 2,
				skin: 'layui-layer-lan',
				area: ['600px', '400px'],
				content : "openUserAdd",//加载某一张页面
				success : function(layero, index){//等同于js异步提交
					setTimeout(function(){
						layui.layer.tips('点击此处返回列表', '.layui-layer-setwin .layui-layer-close', {
							tips: 3
						});
					},500)
				}
			})			
		})
	}).resize();
  
	
	$(window).one("resize",function(){//基于框架做的
		$(".add_btn_cams").click(function(){
			var index = layui.layer.open({
				title : "【添加用户信息】",
				icon: 2,
				type : 2,
				skin: 'layui-layer-lan',
				area: ['600px', '400px'],
				content : "openCamAdd",//加载某一张页面
				success : function(layero, index){//等同于js异步提交
					setTimeout(function(){
						layui.layer.tips('点击此处返回列表', '.layui-layer-setwin .layui-layer-close', {
							tips: 3
						});
					},500)
				}
			})			
		})
	}).resize();
//=======================监听工具条====================================

	//给编辑和删除增加动作，直接应用layui
	table.on('tool(test)', function(obj){ //注：tool是工具条事件名，test是table原始容器的属性 lay-filter="对应的值"
		console.log(obj.field);
	  var data = obj.data; //获得当前行数据
	  var layEvent = obj.event; //获得 lay-event 对应的值（也可以是表头的 event 参数对应的值）
	  var tr = obj.tr; //获得当前行 tr 的DOM对象
	 
	  if(layEvent === 'edit'){ //查看
		  //编辑
		  var index = layui.layer.open({
              title : "【修改信息】",
              type : 2,
              area: ['600px', '400px'],
              content : "openEdit_Users?id="+data.id,
              success : function(layero, index){
                  setTimeout(function(){
                      layui.layer.tips('点击此处返回列表', '.layui-layer-setwin .layui-layer-close', {
                          tips: 3
                      });
                  },500)
              }
          })          
	  
		  
	  }else if(layEvent === 'del'){ //删除
		  layer.confirm('确定删除此信息？',{icon:3, title:'提示信息'},function(index){
				var msgid;
				//向服务端发送删除指令
		 		 $.ajax({//异步请求返回给后台
			    	  url:'deleteUser',
			    	  type:'POST',
			    	  data:{"id":data.id},
			    	  dataType:'json',
			    	  beforeSend: function(re){
			    		  msgid = top.layer.msg('数据处理中，请稍候',{icon: 16,time:false,shade:0.8});
			          },
			    	  success:function(d){
			    		  top.layer.close(msgid);
			    		  if(d.result){
			    			//弹出loading
						   	obj.del(); //删除对应行（tr）的DOM结构，并更新缓存
						  	 //刷新父页面
						   	active_op.reload();
			    		  }else{
			    			  top.layer.msg("操作失败！，数据库操作有问题！！");
			    		  }
				    		
			    	  },
			    	  error:function(XMLHttpRequest, textStatus, errorThrown){
			    		  top.layer.msg('操作失败！！！服务器有问题！！！！<br>请检测服务器是否启动？', {
			    		        time: 20000, //20s后自动关闭
			    		        btn: ['知道了']
			    		      });
			           }
			      });
		 //关闭当前提示	
	      layer.close(index);
	    });
	  } 
	});

	table.on('tool(test1)', function(obj){ //注：tool是工具条事件名，test是table原始容器的属性 lay-filter="对应的值"
	console.log(obj.field);
	  var data = obj.data; //获得当前行数据
	  var layEvent = obj.event; //获得 lay-event 对应的值（也可以是表头的 event 参数对应的值）
	  var tr = obj.tr; //获得当前行 tr 的DOM对象
	  if(layEvent === 'edit'){ //查看
		//编辑
		var index = layui.layer.open({
			title : "【修改信息】",
			type : 2,
			area: ['600px', '400px'],
			content : "openEdit_Cams?id="+data.id,
			success : function(layero, index){
				setTimeout(function(){
					layui.layer.tips('点击此处返回列表', '.layui-layer-setwin .layui-layer-close', {
						tips: 3
					});
				},500)
			}
		})          
	
		
	}else if(layEvent === 'del'){ //删除
		layer.confirm('确定删除此信息？',{icon:3, title:'提示信息'},function(index){
			  var msgid;
			  //向服务端发送删除指令
				$.ajax({//异步请求返回给后台
					url:'deleteCam',
					type:'POST',
					data:{"id":data.id},
					dataType:'json',
					beforeSend: function(re){
						msgid = top.layer.msg('数据处理中，请稍候',{icon: 16,time:false,shade:0.8});
					},
					success:function(d){
						top.layer.close(msgid);
						if(d.result){
						  //弹出loading
							 obj.del(); //删除对应行（tr）的DOM结构，并更新缓存
							 //刷新父页面
							 active_op.reload();
						}else{
							top.layer.msg("操作失败！，数据库操作有问题！！");
						}
						  
					},
					error:function(XMLHttpRequest, textStatus, errorThrown){
						top.layer.msg('操作失败！！！服务器有问题！！！！<br>请检测服务器是否启动？', {
							  time: 20000, //20s后自动关闭
							  btn: ['知道了']
							});
					 }
				});
	   //关闭当前提示	
		layer.close(index);
	  });
	} 
	else if(layEvent === 'add'){ //添加
		var index = layui.layer.open({
			title : "【详细信息】",
			type : 2,
			area: ['600px', '400px'],
			content : "openCamAdd",
			success : function(layero, index){
				setTimeout(function(){
					layui.layer.tips('点击此处返回列表', '.layui-layer-setwin .layui-layer-close', {
						tips: 3
					});
				},500)
			}
		})          
	}
	});
})

