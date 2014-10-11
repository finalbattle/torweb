import cStringIO
import traceback

from torweb.handlers import BaseHandler
import tornado
from soaplib.soap import make_soap_envelope, make_soap_fault, from_soap, collapse_swa, apply_mtom
from soaplib.service import SoapServiceBase
from soaplib.util import reconstruct_url
from soaplib.serializers.primitive import string_encoding, Fault
from soaplib.etimport import ElementTree

from soaplib.service import soapmethod
from soaplib.serializers.primitive import Boolean, Repeating, String, Integer, Double, Float, Null,Array
from soaplib.serializers.binary import Attachment
from soaplib.serializers.clazz import ClassSerializer
_exceptions = False
_exception_logger = None

_debug = False
_debug_logger = None

from code import interact

###################################################################
# Logging / Debugging Utilities                                   #
# replace with python logger?                                     #
###################################################################

def _dump(e): # util?
    print e

def log_exceptions(on, out=_dump):
    global _exceptions
    global _exception_logger

    _exceptions=on
    _exception_logger=out

def log_debug(on,out=_dump):
    global _debug
    global _debug_logger
    
    _debug=on
    _debug_logger=out
    
def debug(msg):
    global _debug
    global _debug_logger
    
    if _debug:
        _debug_logger(msg)
        
def exceptions(msg):
    global _exceptions
    global _exception_logger
    
    if _exceptions:
        _exception_logger(msg)


class SOAPService(BaseHandler, SoapServiceBase):
    '''
    This is the base object representing a soap web application, and conforms
    to the WSGI specification (PEP 333).  This object should be overridden
    and getHandler(environ) overridden to provide the object implementing
    the specified functionality.  Hooks have been added so that the subclass
    can react to various events that happen durring the execution of the
    request.
    '''
    def __init__(self, application, request, **kwargs):
        setattr(self, "request", request)
        setattr(self, "application", application)
        BaseHandler.__init__(self, application, request, **kwargs)
        SoapServiceBase.__init__(self)
    
    def onCall(self,environ):
        '''
        This is the first method called when this WSGI app is invoked
        @param the wsgi environment
        '''
        pass
    
    def onWsdl(self,environ,wsdl):
        '''
        This is called when a wsdl is requested
        @param the wsgi environment
        @param the wsdl string 
        '''
        pass
    
    def onWsdlException(self,environ,exc,resp):
        '''
        Called when an exception occurs durring wsdl generation
        @param the wsgi environment
        @param exc the exception
        @param the fault response string
        '''
        pass
    
    def onMethodExec(self,environ,body,py_params,soap_params):
        '''
        Called BEFORE the service implementing the functionality is called
        @param the wsgi environment
        @param the body element of the soap request
        @param the tuple of python params being passed to the method
        @param the soap elements for each params
        '''
        pass
    
    def onResults(self,environ,py_results,soap_results):
        '''
        Called AFTER the service implementing the functionality is called
        @param the wsgi environment
        @param the python results from the method
        @param the xml serialized results of the method
        '''
        pass
    
    def onException(self,environ,exc,resp):
        '''
        Called when an error occurs durring execution
        @param the wsgi environment
        @param the exception
        @param the response string
        '''
        pass
    
    def onReturn(self,environ,returnString):
        '''
        Called before the application returns
        @param the wsgi environment
        @param return string of the soap request
        '''
        pass
    
    def getHandler(self,environ):
        '''
        This method returns the object responsible for processing a given request, and
        needs to be overridden by a subclass to handle the application specific
        mapping of the request to the appropriate handler.
        @param the wsgi environment
        @returns the object to be called for the soap operation
        '''
        return self
    
    def post(self):
        '''
        This method conforms to the WSGI spec for callable wsgi applications (PEP 333).
        This method looks in environ['wsgi.input'] for a fully formed soap request envelope,
        will deserialize the request parameters and call the method on the object returned
        by the getHandler() method.
        @param the http environment
        @param a callable that begins the response message
        @returns the string representation of the soap call
        '''
        methodname = ''
        container = tornado.wsgi.WSGIContainer(self.application)
        environ = container.environ(self.request)
        try:
            # implementation hook
            self.onCall(environ)
            
            serviceName = environ['PATH_INFO'].split('/')[-1]
            service = self.getHandler(environ)
            if (environ['QUERY_STRING'].endswith('wsdl') or environ['PATH_INFO'].endswith('wsdl')) and environ['REQUEST_METHOD'].lower() == 'get':
                # get the wsdl for the service
                #
                # Assume path_info matches pattern
                # /stuff/stuff/stuff/serviceName.wsdl or ?WSDL
                #
                serviceName = serviceName.split('.')[0]
                url = reconstruct_url(environ).split('.wsdl')[0]
                
                try:
                    wsdl_content = service.wsdl(url)
                    
                    # implementation hook
                    self.onWsdl(environ,wsdl_content)
                except Exception, e:
                    
                    # implementation hook
                    buffer = cStringIO.StringIO()
                    traceback.print_exc(file=buffer)
                    buffer.seek(0)
                    stacktrace = str(buffer.read())
                    faultStr = ElementTree.tostring(make_soap_fault( str(e), detail=stacktrace), encoding=string_encoding)
                    
                    exceptions(faultStr)
                    
                    self.onWsdlException(environ,e,faultStr)
                    
                    # initiate the response
                    #return Response(faultStr, '500 Internal Server Error', [('Content-type','text/xml;charset=utf-8')])
                    self.set_header('Content-Type', 'text/xml;charset=utf-8')
                    return self.write(faultStr)
                
                #return Response(wsdl_content, '200 OK', [('Content-type','text/xml;charset=utf-8')])
                self.set_header('Content-Type', 'text/xml;charset=utf-8')
                return self.write(wsdl_content)
            if environ['REQUEST_METHOD'].lower() != 'post':
                #return Response('', '405 Method Not Allowed',[('Allow','POST')])
                self.set_header('Content-Type', 'text/html;charset=utf-8')
                return self.write_error(status_code=405)
                
            input = environ.get('wsgi.input')
            length = environ.get("CONTENT_LENGTH")
            body = input.read(int(length))
            debug(body)
            # body, _unmentioned_attachs = collapse_swa( environ.get("CONTENT_TYPE"), body)
            # collapse_swa has some problem
            try:
                body, _unmentioned_attachs = collapse_swa( environ.get("CONTENT_TYPE"), body)
            except:
                body = collapse_swa( environ.get("CONTENT_TYPE"), body)
                _unmentioned_attachs = []
                pass
            # deserialize the body of the message
            try:
                payload, header = from_soap(body)
            except SyntaxError,e:
                payload = None
                header = None

            if payload is not None:
                methodname = payload.tag.split('}')[-1]
            else:
                # check HTTP_SOAPACTION
                methodname = environ.get("HTTP_SOAPACTION")
                if methodname.startswith('"') and methodname.endswith('"'):
                    methodname = methodname[1:-1]
                if methodname.find('/') >0:
                    methodname = methodname.split('/')[1]

            # call the method
            func = getattr(service, methodname)
            
            # retrieve the method descriptor
            descriptor = func(_soap_descriptor=True, klazz=service.__class__)
            if payload is not None:
                params = descriptor.inMessage.from_xml(*[payload])
            else:
                params = ()
            # implementation hook
            self.onMethodExec(environ,body,params,descriptor.inMessage.params)
            
            # call the method
            if len(_unmentioned_attachs) > 0:
            	retval = func(*params, unmentioned_attachs = _unmentioned_attachs)
            else:
            	retval = func(*params)
            
            # transform the results into an element
            # only expect a single element
            results = None
            if not (descriptor.isAsync or descriptor.isCallback):
                results = descriptor.outMessage.to_xml(*[retval])

            # implementation hook
            self.onResults(environ,results,retval)
            
            # construct the soap response, and serialize it
            envelope = make_soap_envelope(results,tns=service.__tns__) 
            #ElementTree.cleanup_namespaces(envelope)
            resp = ElementTree.tostring(envelope, encoding=string_encoding)
            headers = {'Content-Type': 'text/xml;charset=utf-8'}

            if descriptor.mtom:
                headers, resp = apply_mtom( headers, resp,
                                            descriptor.outMessage.params,
                                            (retval,) )

            resp = '<?xml version="1.0" encoding="utf-8"?>' + resp  
            if environ.has_key('CONTENT_LENGTH'):
                del(environ['CONTENT_LENGTH'])
                
            self.onReturn(environ,resp)
            debug(resp)
            
            # return the serialized results
            #return Response(resp, '200 OK', headers.items())
            self.set_header('Content-Type', 'text/xml;charset=utf-8')
            return self.write(resp)
        
        except Fault,e:
        
            # The user issued a Fault, so handle it just like an exception!
            fault = make_soap_fault(
                e.faultstring,
                e.faultcode,
                e.detail)
                
            faultStr = ElementTree.tostring(fault, encoding=string_encoding)
            exceptions(faultStr)
            
            self.onException(environ,e,faultStr)
            
            # initiate the response
            #return Response(faultStr, '500 Internal Server Error',[('Content-type','text/xml;charset=utf-8')])
            self.set_header('Content-Type', 'text/xml;charset=utf-8')
            return self.write(faultStr)
        
        except Exception, e:
            # Dump the stack trace to a buffer to be sent
            # back to the caller
            
            # capture stacktrace
            buffer = cStringIO.StringIO()
            traceback.print_exc(file=buffer)
            buffer.seek(0)
            stacktrace = str(buffer.read())
            
            faultstring = str(e)
            if methodname:
                faultcode = faultCode='%sFault'%methodname
            else:
                faultcode = 'Server'
            detail = stacktrace
            
            faultStr = ElementTree.tostring(make_soap_fault(faultstring,faultcode,detail), encoding=string_encoding)            
            exceptions(faultStr)
            
            self.onException(environ,e,faultStr)
            
            # initiate the response
            print faultStr
            #return Response(faultStr, '500 Internal Server Error', [('Content-type','text/xml;charset=utf-8')])
            self.set_header('Content-Type', 'text/xml;charset=utf-8')
            return self.write(faultStr)
    
    def get(self):
        return self.post()
