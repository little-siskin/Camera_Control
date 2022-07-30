layui.extend({
	admin: '{/}../statics/js/admin'
});
layui.use(['laydate', 'jquery', 'admin'], function() {
	var laydate = layui.laydate,
		$ = layui.jquery,
		admin = layui.admin;
	//执行一个laydate实例
	laydate.render({
		elem: '#start' //指定元素
	});
	//执行一个laydate实例
	laydate.render({
		elem: '#end' //指定元素
	});
	/*用户-停用*/
	window.member_stop = function (obj) {
		var data = obj.data;
		var i=$(obj).attr('title');
		console.log(i);
		$.ajax({//异步请求返回给后台
	    	  url:'control/',
	    	  type:'POST',
		       data:{id:i},
	    	  dataType:'json',
	    	  // beforeSend: function(re){
	    		//   index = top.layer.msg('启动中',{icon: 16,time:false,shade:0.8});
	          // },
	          success:function(d){
	    	  		console.log(data);
	        	  	var r=d.result;
	        	  	console.log(r);
	        	  		if(r==0){
							$(obj).find('i').html('&#xe601;');
							$(obj).attr('title', '启用')
					  		$(obj).parents("tr").find(".td-status").find('span').addClass('layui-btn-disabled').html('已停用');
		        	  	}
		        	  	else if(r==1){
		        	  		$(obj).find('i').html('&#xe62f;');
		        	  		$(obj).attr('title', '停用')
		        	  		$(obj).parents("tr").find(".td-status").find('span').removeClass('layui-btn-disabled').html('已启用');
		        	  	}
	           }
 		 })
		 return false;
	}


});